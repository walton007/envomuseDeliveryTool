# -*- coding: utf-8 -*-

__author__ = 'jun'

import threading
import json
from db import DBConn

class Sync(threading.Thread):
    def __init__(self,srvAddr=None,conn=None,session=None):
        threading.Thread.__init__(self)

        self.conn = conn if conn is not None else DBConn()
        self.srvAddr = srvAddr if srvAddr is not None else "http://localhost:9000"
        self.apiUrl = '/itapi/exportRequests/'
        self.session = session

        self.localTracks = []
        self.localPrograms = []
        self.remotePrograms = []
        self.remoteTracks = []
        self.channels = set()
        self.trackIdx = 0
        # self.cacheMedia()

    def run(self):
        db = DBConn()
        self.cacheMedia(db)

    def dosync(self):
        self.getLocalProgramList()
        self.getLocalTrackList()
        self.getRemoteProgramList()
        self.updateLocalDBProgram()
        self.updateStores()

    def setTrackIdx(self,n):
        self.trackIdx = n

    def getTrackIdx(self):
        return self.trackIdx

    def getRemoteProgramTotalCount(self):
        # print(len(self.remotePrograms))
        return len(self.remotePrograms)

    def getRemoteTrackTotalCount(self):
        # print(len(self.remoteTracks))
        return len(self.remoteTracks)

    def getLocalProgramList(self):
        pgl = self.conn.getProgramList()
        if pgl is not None:
            self.localPrograms = [x[0] for x in pgl]

    def getLocalTrackList(self):
        tl = self.conn.getTrackList()
        if tl is not None:
            self.localTracks = [x[0] for x in tl]

    def getRemoteProgramList(self):
        pgmList = self.session.get(self.srvAddr+self.apiUrl)
        # print(pgmList)
        try:
            pl = pgmList.json()
            # print(pl)
            for p in pl:
                print(p)
                r = self.getRemoteProgramDetail(pid=p['_id'])
                self.channels.add(r['channelId'])
                self.remotePrograms.append(r)

        except Exception as e:
            print(e)

    def getRemoteProgramDetail(self,pid=None):
        r = self.session.get(self.srvAddr+self.apiUrl+pid)
        try:
            pd = r.json()
            return {'pid':pd['program'],
                        'pname':pd['programName'],
                        'pstartDate':pd['startDate'],
                        'pendDate':pd['endDate'],
                        'channelId':pd['channel'],
                        'playlistOriginal':pd['dayPlaylistArr'],
                        'trackList':[]
                        }

        except Exception as e:
            print(e)

    def updateLocalDBProgram(self):
        #get clean music list
        tmpTrackList = []
        trackIdList = set()
        for p in self.remotePrograms:
            for t in p['playlistOriginal']:
                tmp = {'date':t['date'],'playlist':[]}
                for i in t['playlist']:
                    tmp['playlist'].append(i['track'])
                    if i['track'] in self.localTracks:
                        pass #pass local tracks
                    else:
                        if i['track'] not in trackIdList: #pass duplicated tracks
                            trackIdList.add(i['track'])
                            tmpTrackList.append((i['track'],i['name'],i['duration'],0,0,))
                p['trackList'].append(tmp)

        self.remoteTracks = tmpTrackList
        self.conn.addTracks(tmpTrackList)
        self.getLocalTrackList()

        #get simplified playlist of each program
        pgmList = []
        for p in self.remotePrograms:
            if p['pid'] not in self.localPrograms:
                pgmList.append((p['pid'],p['pname'],p['pstartDate'],p['pendDate'],p['channelId'],json.dumps(p['trackList']),json.dumps(p['playlistOriginal'])))

        self.conn.addPrograms(pgmList)
        self.getLocalProgramList()

    def getStoresByChannelId(self,cid=None):
        r = self.session.get(self.srvAddr+'/itapi/channels/'+cid+'/sites')
        try:
            stores = r.json()
            if len(stores)>0:
                return stores
            else:
                print("Calling Stores API: no store found.")
                return None
        except:
            pass

    def updateStores(self):
        '''
        function to update stores table using channels id set
        :return:
        '''
        if len(self.channels)>0 :
            for c in self.channels:
                s = self.getStoresByChannelId(c)
                if s is not None:
                    st_lst = [(x['_id'] if '_id' in x else '',
                               x['siteName'] if 'siteName' in x else '',
                               x['reference'] if 'reference' in x else '',
                               x['deviceId'] if  'deviceId' in x else '',
                               c,
                               s['channelName'] if 'channelName' in s else '',
                               x['brandId'] if 'brandId' in x else '',
                               x['brandName'] if 'brandName' in x else '',
                               x['license']['uuid'] if 'license' in x else '')
                              for x in s['sites']]

                    if len(st_lst) > 0:
                        self.conn.clearStores(c)
                        self.conn.addStores(st_lst)
                    else:
                        print("No store found, skipping...")
                else:
                    print("No store found, skipping...")

        else:
            print("No Channels found, nothing to update.")

    def cacheMedia(self,db):
        '''
        download media files from remote server using FTP
        :return:
        '''
        print("Starting media file downloading...")
        tracks = set(self.localTracks)

        for t in tracks:
            tv = db.getTrackById(t)
            if tv is not None and tv[3]==0:
                m=self.session.get(self.srvAddr+'/itapi/tracks/'+tv[0]+'/hqfile',stream=True)
                file_name = '../media/'+tv[0]+'.'+tv[1].split('.')[-1]
                with open(file_name, 'wb') as f:
                    for chunk in m.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()

                db.updateTrackCacheStatusById(tv[0])
                self.setTrackIdx(self.getTrackIdx()+1)
                print(tv[1]+' is downloaded...')

if __name__ == '__main__':
    s = Sync()