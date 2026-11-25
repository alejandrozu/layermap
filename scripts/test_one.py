import sys, time, json
sys.path.insert(0,'/home/claude/scripts')
from build_country import build, write
from groups import *
iso='NGA'
levels=[{'label':('Geopolitical zone','Geopolitical zones'),'group':NGA_ZONES},
        {'label':('State','States'),'geo':[('gb','NGA','ADM1')]},
        {'label':('Local government area','Local government areas'),'geo':[('gb','NGA','ADM2')]}]
t=time.time(); log=[]
fin,counts,names,parents=build(iso,levels,log=log)
e=write(iso,levels,fin,counts,names,parents,log=log)
print('\n'.join(log)); print(e, round(time.time()-t,1),'s')
