import numpy as np
from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from datetime import  *
import pdb
import sys
import os

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

def set_grid(sNcFile,time_line,ds):

    ncfile = Dataset(sNcFile,'r')

    # variable extraction
    lats = ncfile.variables['latitude'][time_line,:]
    lons = ncfile.variables['longitude'][time_line,:]

    # generate output grid
    grid_min_longitude = np.min(lons)-ds
    grid_min_latitude = np.min(lats)-ds
    grid_max_longitude = np.max(lons)+ds
    grid_max_latitude = np.max(lats)+ds
    
    return grid_min_longitude,grid_max_longitude,grid_min_latitude,grid_max_latitude
    
################################################################################
# USER INPUTS
################################################################################
# where are the simulation outputs and main output file?
input_folder = 'INPFOLD'
sNcFile = (input_folder + '/spill_properties.nc')

time_index=np.arange(0,DURA,1)

iStartDay = date(INPYY,INPMM,INPDD).toordinal()
iStartHour = INPHH
iStartMinute = MUNIT

real_time = time_index/24. + (iStartHour+1.)/24. + iStartDay

# set where your coastline-support file is located
# OBS: the file should have been generated by preproc_gshhs_MDK2.py
coast_file = 'BATFOLD/dtm.txt' 

# set output folder where .png files will be placed
output_folder = input_folder
os.system('mkdir ' + output_folder)
################################################################################
# From here onwards, the script should do everything pretty much automatic
# bugs/errors are expected and in case you unfortunate enough to find out one,
# feel free to send us comments/corrections.

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

grid_min_longitude,grid_max_longitude,grid_min_latitude,grid_max_latitude = set_grid(sNcFile,time_index,.15/110)

geo_buffer=0
    	
if np.logical_or((grid_max_latitude-grid_min_latitude)<1,(grid_max_longitude-grid_min_longitude)<1):
	geo_buffer=.1
    		
#if np.abs(grid_max_latitude-grid_min_latitude)<1:
#	grid_min_latitude=grid_min_latitude-.5
#	grid_max_latitude=grid_max_latitude+.5
    		
#if np.abs(grid_max_longitude-grid_min_longitude)<1:
#	grid_min_longitude=grid_min_longitude-.5
#	grid_max_longitude=grid_max_longitude+.5
    		
#if grid_min_latitude<-90:
#	grid_min_latitude=-90
    		
#if grid_max_latitude>90:
#	grid_max_latitude=90

#if grid_min_longitude<-180:
#	grid_min_longitude=-180
#if grid_max_longitude>180:
#	grid_max_longitude=180   
    		
print('MEDSLIK-II grid boundaries')
print('')
print('LatMin: ',grid_min_latitude)
print('LatMax: ',grid_max_latitude)
print('LonMin: ',grid_min_longitude)
print('LonMax: ',grid_max_longitude)
   
# prepare basemap   	
m = Basemap(llcrnrlon=grid_min_longitude-geo_buffer,llcrnrlat=grid_min_latitude-geo_buffer,\
            urcrnrlon=grid_max_longitude+geo_buffer,urcrnrlat=grid_max_latitude+geo_buffer,\
            rsphere=(6378137.00,6356752.3142),\
            resolution='f',projection='merc',\
            lat_0=(grid_max_latitude + grid_min_latitude)/2.,\
			lon_0=(grid_max_longitude + grid_min_longitude)/2.,epsg=4326)#4232)  

x0,y0 = m(x0,y0)    

# prepare segment positions
iTargetSites = np.loadtxt(coast_file)
iTargetSites = iTargetSites[(iTargetSites[:,1]>grid_min_latitude),:]
iTargetSites = iTargetSites[(iTargetSites[:,0]>grid_min_longitude),:]
iTargetSites = iTargetSites[(iTargetSites[:,1]<grid_max_latitude),:]
iTargetSites = iTargetSites[(iTargetSites[:,0]<grid_max_longitude),:]
iSegmentLengths=haversine(iTargetSites[:,0],iTargetSites[:,1],iTargetSites[:,2],iTargetSites[:,3])

# extract values of interest
cc=0
for ii in time_index:
    
    print ('Generating outputs ' +  '%03d' % (ii+1) + 'h.png')
    
    print ('...loading nc file - time step...')    
    # lon, lat and status for each oil parcel at time step ii
    lats = ncfile.variables['latitude'][ii,:]
    lons = ncfile.variables['longitude'][ii,:]
    particle_status = ncfile.variables['particle_status'][ii,:]


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

    # Setting time
    jday = np.floor(real_time[cc])
    hh = np.round((real_time[cc]-jday)*24)
    if hh == 0:
        full_date = date.fromordinal(int(jday-1))
        YY = full_date.strftime('%y')
        mm = full_date.strftime('%m')
        dd = full_date.strftime('%d')
        hh = 24
    else:
        full_date = date.fromordinal(int(jday))
        YY = full_date.strftime('%y')
        mm = full_date.strftime('%m')
        dd = full_date.strftime('%d')
	
	
    print ('...plotting results...') 
    if len(iCP>0):	
        aa=np.argwhere(iCP>0)
        x_m=(iTargetSites[:,0]+iTargetSites[:,2])/2.
        y_m=(iTargetSites[:,1]+iTargetSites[:,3])/2.

        x_m,y_m=m(x_m,y_m)
        sorted_concs=np.argsort(iCP)
   
        for ss in sorted_concs:
            ax1=plt.subplot(111)           

            if iCP[ss]>0:
                cs = plt.scatter(x_m[ss],y_m[ss], s=(iCP[ss]/np.max(iCP))*80, c = iCP[ss], vmin = np.percentile(iCP[aa],5), vmax = np.percentile(iCP[aa],95),edgecolor='',alpha=0.3,cmap='gist_rainbow')                
                cbar = m.colorbar(cs,location='bottom',pad=0.2)
                cbar.set_label('tons/km')
                cbar.ax.tick_params(labelsize=4)


    m.plot(x0,y0,'k+',markersize=5)
    
    # Plot coastlines
    m.drawcoastlines(linewidth=0.05)
    #m.fillcontinents(alpha=0.1)
    m.drawmeridians(np.arange(grid_min_longitude-geo_buffer,grid_max_longitude+geo_buffer,(grid_max_longitude-grid_min_longitude+2*geo_buffer)/4.),labels=[0,0,0,1],color='white',linewidth=0.03,fontsize = 8) # draw parallels
    m.drawparallels(np.arange(grid_min_latitude-geo_buffer,grid_max_latitude+geo_buffer,(grid_max_latitude-grid_min_latitude+2*geo_buffer)/4.),labels=[1,0,0,0],color='white',linewidth=0.03,fontsize = 8) # draw meridians
    
    plt.title('Beached oil concentrations for '+ dd + '.' + mm + '.20' + YY + ' ' + '%02d' % (hh) + ':' + '%02d' % (iStartMinute) + ' UTC')
    plt.savefig(output_folder + '/beached_oil_' + '%03d' % (ii+1) + 'h.png',bbox_inches='tight',dpi=300)
    print('Output has been saved')    
    plt.close('all')
    cc = cc + 1      

    
    
