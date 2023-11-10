import numpy as np
from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from datetime import  *
import pdb
import sys
#from mpl_toolkits.axes_grid1 import make_axes_locatable

"""
Application:
    This script has been developed to plot oil concentrations found at the 
    coast based on MEDSLIK II outputs. The outputs are png figures.
"""

def haversine(lon1, lat1, lon2, lat2):
	"""
	Calculate the great circle distance between two points
	on the earth (specified in decimal degrees). Taken from stackoverflow, thanks to Michael Dunn!
	http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
	"""
	# convert decimal degrees to radians
	lon1=np.radians(lon1)
	lon2=np.radians(lon2)
	lat1=np.radians(lat1)
	lat2=np.radians(lat2)

	# haversine formula
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
	c = 2 * np.arcsin(np.sqrt(a))

	# 6367 km is the radius of the Earth
	km = 6367 * c
	return km


def dist(point,segments): # x3,y3 is the point

	x1=segments[:,0]
	x2=segments[:,2]
	y1=segments[:,1]
	y2=segments[:,3]
	x3=point[0]
	y3=point[1]
	px = x2-x1
	py = y2-y1
	something = px*px + py*py
	u =  ((x3 - x1) * px + (y3 - y1) * py) / something
	u[np.argwhere(u>1)]=1
	u[np.argwhere(u<0)]=0
	x = x1 + u * px
	y = y1 + u * py
	dx = x - x3
	dy = y - y3
	dist = np.sqrt(dx*dx + dy*dy)

	return dist

################################################################################
# USER INPUTS
################################################################################
# set file containing MEDSLIK II netcdf outputs
#sNcFile = ('/Users/asepp/work/paria/RELOCATABLE_2017_04_24_1300_case_study2/spill_properties.nc')
sNcFile = ('/Users/asepp/work/tests_preconf/RELOCATABLE_2017_04_24_1300_case_study3/spill_properties.nc')
# set time steps of interest (hours by default -- Python counting starts from 0).
# It may be a single number e.g. [146] or a list of numbers e.g. np.arange(0,15)
time_index=np.arange(0,120,6)#np.arange(35,120,6)

# set where your coastline-support file is located
# OBS: the file should have been generated by preproc_gshhs_MDK2.py
coast_file = '/Users/asepp/work/data/paria/bnc_files/medf.txt'

# set output folder where .png files will be placed
output_folder = '/Users/asepp/work/paria/outputs/'

################################################################################
# USER INPUTS - OVER!
################################################################################
# From here onwards, the script should do everything pretty much automatic
# bugs/errors are expected and in case you unfortunate enough to find out one,
# feel free to send us comments/corrections.

# prepare segment positions
iTargetSites = np.loadtxt(coast_file)
iTargetSites = iTargetSites[(iTargetSites[:,1]>10.45),:]
iTargetSites = iTargetSites[(iTargetSites[:,0]>-64.5),:]
iTargetSites = iTargetSites[(iTargetSites[:,1]<11.3),:]
iTargetSites = iTargetSites[(iTargetSites[:,0]<-63.5),:]
iSegmentLengths=haversine(iTargetSites[:,0],iTargetSites[:,1],iTargetSites[:,2],iTargetSites[:,3])

# load MEDSLIK netCDF output file
ncfile= Dataset(sNcFile,'r')

# bbl2tonne converter
oil_density = ncfile.variables['non_evaporative_volume'].oil_density
parcel_volume = ncfile.variables['non_evaporative_volume'].volume_of_parcel
rbm3=0.158987
barrel2tonnes=1/(rbm3*(oil_density/1000))

# find the origin of the spill
y0 = ncfile.variables['non_evaporative_volume'].initial_position_y
x0 = ncfile.variables['non_evaporative_volume'].initial_position_x
print ("Spill initial location = " + str(x0) + "W ::::: " + str(y0) + "N ")

# define map boundaries
dt = np.max(time_index)
max_ds = (dt*.6)/110
grid_min_longitude = x0 - max_ds
grid_min_latitude = y0 - max_ds
grid_max_longitude = x0 + max_ds
grid_max_latitude = y0 + max_ds

# extract values of interest
cc = 0
for ii in time_index:
    
    print ('Generating outputs ' +  '%03d' % (ii+1) + 'h.png')
    
    print ('...loading nc file - time step...')    
    # lon, lat and status for each oil parcel at time step ii
    lats = ncfile.variables['latitude'][ii,:]
    lons = ncfile.variables['longitude'][ii,:]
    particle_status = ncfile.variables['particle_status'][ii,:]
    pdb.set_trace()

    print ('...searching for beached parcels...') 
    # removing parcels other than beached
    iNoise=np.argwhere(particle_status >= 0)
    lats = np.delete(lats, (iNoise), axis=0)
    lons = np.delete(lons, (iNoise), axis=0)
    particle_status = np.delete(particle_status, (iNoise), axis=0)
    iBeaching=(np.transpose(lons),np.transpose(lats),np.transpose(particle_status))
    
    # output matrices
    iAssignedSegment=np.zeros(np.shape(lons)[0])
    iConcentrationsParcels=np.zeros(len(iTargetSites))
    iCP=np.zeros(len(iTargetSites))

    print ('...assigning parcels to coastal segments...') 
    # assign a target site to the beached parcels
    for jj in range(0,np.shape(lons)[0]):
        iParcelPosition=(iBeaching[0][jj],iBeaching[1][jj])
        iParcelDistance=dist(iParcelPosition,iTargetSites)
        iParcelDistance[np.isnan(iParcelDistance)]=9999 # border segments are removed
        iClosestSegmentDist=np.min(iParcelDistance)

        if iClosestSegmentDist<.1/110:
            if len(np.argwhere(iParcelDistance==iClosestSegmentDist))>1:
                iAssignedSegment[jj]=np.argwhere(iParcelDistance==iClosestSegmentDist)[0]

            else:
                iAssignedSegment[jj]=np.argwhere(iParcelDistance==iClosestSegmentDist)

        iObservedOil=((-iBeaching[2][jj])/iSegmentLengths[int(iAssignedSegment[jj])])/barrel2tonnes
        iCP[int(iAssignedSegment[jj])]=iObservedOil


    if cc == 0:

        print('...starting mapping...')
        # start basemap
        m = Basemap(llcrnrlon=grid_min_longitude,llcrnrlat=grid_min_latitude,\
            urcrnrlon=grid_max_longitude,urcrnrlat=grid_max_latitude,\
            rsphere=(6378137.00,6356752.3142),\
            resolution='f',projection='merc',\
            lat_0=(grid_max_latitude + grid_min_latitude)/2,\
			lon_0=(grid_max_longitude + grid_min_longitude)/2)
        x0,y0 = m(x0,y0)
        cc =  cc +1

  

	# Plot coastlines
    m.drawcoastlines(linewidth=0.05)
    m.fillcontinents(alpha=0.1)
    
    m.drawmeridians(np.arange(grid_min_longitude-.1,grid_max_longitude+.101, \
        ((grid_max_longitude+.101)-(grid_min_longitude-.1))/3),\
        labels=[0,0,0,1],color='black',linewidth=0.03) # draw parallels
    m.drawparallels(np.arange(grid_min_latitude-.1,grid_max_latitude+.101, \
		((grid_max_latitude+.101)-(grid_min_latitude-.1))/3), \
		labels=[1,0,0,0],color='black',linewidth=0.03) # draw meridians

    print ('...plotting results...') 
    if len(iCP>0):
        aa=np.argwhere(iCP>0)
        x_m=(iTargetSites[:,0]+iTargetSites[:,2])/2
        y_m=(iTargetSites[:,1]+iTargetSites[:,3])/2

        x_m,y_m=m(x_m,y_m)
        sorted_concs=np.argsort(iCP)
   
        for ss in sorted_concs:
            ax1=plt.subplot(111)           

            if iCP[ss]>0:
                cs = plt.scatter(x_m[ss],y_m[ss], s=(iCP[ss]/np.max(iCP))*80, c = iCP[ss], vmin = np.percentile(iCP[aa],5), vmax = np.percentile(iCP[aa],95),edgecolor='',alpha=0.3,cmap='gist_rainbow')                
                cbar = m.colorbar(cs,location='bottom',pad=0.2)#pad="5%")
                cbar.set_label('tons/km')

    m.plot(x0,y0,'k+',markersize=5)
    plt.title('Beached oil concentrations for '+ '%03d' % (ii+1) + 'h')
    #plt.savefig(output_folder + '/beached_oil_' + '%03d' % (ii+1) + 'h.png',bbox_inches='tight',dpi=300)
    print('Output has been saved')    
    plt.show()
    plt.close('all')

    
    
