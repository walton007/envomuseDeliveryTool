# -*- coding: utf-8 -*-


__author__ = 'jun'

from tkinter import *
from tkinter.ttk import *
import json
from PIL import Image, ImageTk
from datetime import datetime
from datetime import timedelta
import os
import os.path
import shutil
import glob
from db import DBConn

class EnvoMaster(Frame):
    def __init__(self,master=None,controller=None,conn=None):
        print("initializing main interface...")

        self.conn = conn if conn is not None else DBConn()
        self.programList = []
        self.programTrackList = []

        Frame.__init__(self,master)
        self.grid(column=0,row=0,sticky="NWSE")

        self.columnconfigure(0, weight=0,minsize=200)
        self.columnconfigure(1, weight=1,minsize=200)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1,minsize=400)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1,minsize=200)

        self.brandName = StringVar()
        self.programName = StringVar()
        self.channelName = StringVar()
        self.timePeriod = StringVar()
        self.totalTracks = StringVar()
        self.totalStores = StringVar()
        # self.totalTracks = IntVar()
        # self.totalStores = IntVar()

        self.chosenProgramId = None

        banner = Frame(self)
        self.logo = ImageTk.PhotoImage(Image.open('./logo.jpeg'))
        self.label = Label(banner,image=self.logo)
        self.label.image = self.logo
        self.label.pack(side=LEFT,expand=True,fill=BOTH)
        banner.grid(row=0,column=0,columnspan=2,sticky="WE")

        self.programTree = Treeview(self)
        self.programTree.bind('<<TreeviewSelect>>',self.popProgramTrackList)
        self.programTree['columns']=('exported')
        self.programTree.column('exported',width=50)
        self.programTree.heading('exported',text="导出状态")
        self.programTree.grid(row=1,column=0,sticky=(N, W, S))

        self.programTrackTreeContainer = Frame(self)
        self.programTrackTreeContainer.grid(row=1,column=1,sticky="NWSE")

        self.programTrackTree = Treeview(self.programTrackTreeContainer,show="headings")
        self.programTrackTree.bind('<<TreeviewSelect>>',self.selectTrack)
        self.programTrackTree['columns']=('id','name','duration','starttime','box','cached')
        self.programTrackTree.column('id',width=40)
        self.programTrackTree.column('name',width=300)
        self.programTrackTree.column('duration',width=100)
        self.programTrackTree.column('starttime',width=100)
        self.programTrackTree.column('box',width=150)
        self.programTrackTree.column('cached',width=100)
        self.programTrackTree.heading('id',text='#')
        self.programTrackTree.heading('name',text='歌曲名')
        self.programTrackTree.heading('duration',text='时长')
        self.programTrackTree.heading('starttime',text='当天开始时间')
        self.programTrackTree.heading('box',text='曲风盒')
        self.programTrackTree.heading('cached',text='同步完成')

        self.vsb = Scrollbar(self.programTrackTreeContainer,orient="vertical", command=self.programTrackTree.yview)
        self.hsb = Scrollbar(self.programTrackTreeContainer,orient="horizontal", command=self.programTrackTree.xview)
        self.programTrackTree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.programTrackTree.pack(side=LEFT,fill=BOTH,expand=True)
        self.hsb.pack(side=BOTTOM,fill=X)
        self.vsb.pack(side=RIGHT,fill=Y)

        # # self.programTrackTree.grid(row=1,column=1,columnspan=3,sticky=(N, W, E, S))
        # self.vsb.grid(row=1,column=4,sticky='ns')
        # self.hsb.grid(row=2,column=1,sticky='ew')

        self.bottomFrame = Frame(self,relief=RIDGE,padding=5,borderwidth=1)
        self.bottomFrame.grid(row=3,column=0,columnspan=2,sticky=(N,S,W,E),padx=5)
        Label(self.bottomFrame,text="客户",width=20).grid(column=0,row=0,sticky=(NW))
        Label(self.bottomFrame,text="频道").grid(column=0,row=1,sticky=(W))
        Label(self.bottomFrame,text="门店").grid(column=0,row=2,sticky=(W))
        Label(self.bottomFrame,text="PROGRAM",width=20).grid(column=2,row=0,sticky=(N))
        Label(self.bottomFrame,text="时间区间").grid(column=2,row=1,sticky=(W))
        Label(self.bottomFrame,text="曲目数").grid(column=2,row=2,sticky=(W))
        Label(self.bottomFrame,textvariable=self.brandName).grid(column=1,row=0,sticky=(NW),padx=5)
        Label(self.bottomFrame,textvariable=self.channelName).grid(column=1,row=1,sticky=(W),padx=5)
        Label(self.bottomFrame,textvariable=self.totalStores).grid(column=1,row=2,sticky=(W),padx=5)
        Label(self.bottomFrame,textvariable=self.programName).grid(column=3,row=0,sticky=(N),padx=5)
        Label(self.bottomFrame,textvariable=self.timePeriod).grid(column=3,row=1,sticky=(W),padx=5)
        Label(self.bottomFrame,textvariable=self.totalTracks).grid(column=3,row=2,sticky=(W),padx=5)

        self.exportBtn = Button(self.bottomFrame,text="开始交付",command=self.export)
        self.exportBtn.grid(column=4,row=3,rowspan=2,sticky=(E),padx=5,pady=5)

        self.clearBtn = Button(self.bottomFrame,text="Clear",command=self.clear)
        self.clearBtn.grid(column=5,row=3,rowspan=1,sticky=(E),padx=5,pady=5)

    def clear(self):
        self.conn.clear()

    def onShow(self):
        # self.pack()
        self.popProgramList()

    def popProgramList(self):
        self.programTree.delete(*self.programTree.get_children())

        tmp = self.conn.getProgramListMeta()
        for t in tmp:
            self.programList.append(dict(zip(('id','name','start','end','export'),t)))

        for p in self.programList:
            if not self.programTree.exists(p['id']):
                # n = self.programTree.insert('','end',p['id'],text=p['name'])
                n = self.programTree.insert('','end',p['id'],text=p['name'],values=('已导出' if p['export']==1 else ''))
                stDate = datetime.strptime(p['start'][:10],'%Y-%m-%d')
                endDate = datetime.strptime(p['end'][:10],'%Y-%m-%d')
                dtIdx = stDate
                step = timedelta(days=1)
                while dtIdx<=endDate:
                    dtIdxStr = datetime.strftime(dtIdx,'%Y-%m-%d')
                    self.programTree.insert(p['id'],'end',p['id']+'|'+dtIdxStr,text=dtIdxStr)
                    dtIdx+=step

    def popProgramTrackList(self,event):
        item = self.programTree.selection()[0]
        pid = None
        dt = None
        tracks = None

        if '|' in item:
            idx = item.index('|')
            pid = item[:idx]
            dt = item[(idx+1):]
        else:
            pid = item

        pgmDetail = self.conn.getProgramTrackList(pid)

        self.programName.set(pgmDetail[1])
        self.timePeriod.set(pgmDetail[2][:10]+' -> '+pgmDetail[3][:10])
        self.channelName.set(pgmDetail[5])

        self.chosenProgramId = pid
        self.chosenChannelId = pgmDetail[5]

        # print(pgmDetail)

        tracks = self._getCleanTrackList(json.loads(pgmDetail[6]),pid,dt)

        print("Cleaning current list...")
        self.programTrackTree.delete(*self.programTrackTree.get_children())
        print("Cleaning work done...")

        if tracks is not None:
            self._insertTracks(tracks,dt)

    def _insertTracks(self,tracks,dt):

        print(tracks)
        if dt is not None:
            idx = 0
            for t in tracks:
                idx+=1
                cached = self.conn.getTrackCacheStatus(t['track'])
                # print(cached[0][0])
                cached = cached[0][0]
                item = (idx,t['name'],t['duration'],t['exactPlayTime'],t['fromBoxs'][0],"完成" if cached==1 else "")
                self.programTrackTree.insert('','end',values=item)
        else:
            pass

    def _getCleanTrackList(self,tracks,pid,dt):
        if dt is not None: #chosen a specific date
            for i in tracks:
                if i['date'][:10] == dt:
                    tracks=i['playlist']
        else: #chosen root node
            tracks=[(x['date'],x['playlist']) for x in tracks ]

        return tracks

    def selectTrack(self,event):
        # item = self.programTrackTree.item(self.programTrackTree.selection()[0])
        # print(item)
        pass

    def reload(self):
        pass

    def export(self):
        pgm = self.conn.getProgramTrackForExport(self.chosenProgramId)

        str_pgmName = pgm[1]
        str_bdName = '未知客户' if pgm[2] is None else pgm[2]
        str_dt = datetime.strftime(datetime.today(),'%Y%m%d')
        track_id_lst = {b for i in json.loads(pgm[3]) for b in i['playlist']}
        playlist_data = json.loads(pgm[4])

        params = (str_dt,str_bdName,str_pgmName)

        #get all stores binded to the channel
        stores = self.conn.getStoresByChannelId(self.chosenChannelId)

        if stores:
            print(stores)
            for s in stores:
                self._generateExportFile(params,track_id_lst,playlist_data,s)
                self.conn.updateProgramExportStatus(self.chosenProgramId)
                print(s[2]+' export done!')

        else:
            print("No stores associated...")

        self.popProgramList()

    def _generateExportFile(self,params,tracklist,playlist_data,store):
        storeRoot = '../delivery/'+params[0]
        p = '_'.join([params[0],params[1],params[2],store[2]])
        storePath = '../delivery/'+params[0]+'/'+p
        mediaPath = storePath+'/cache'
        mediaSrcPath = '../media/'

        if os.path.exists(storePath):
            print("Directory exists, skipping...")
            pass
        else:
            os.makedirs(storePath,exist_ok=True)
            os.makedirs(mediaPath,exist_ok=True)

            #save playlist file
            with open(storePath+'/playlist.env','w+') as f:
                f.write(json.dumps(playlist_data))

            with open(storePath+'/meta.env','w+') as f:
                f.write(json.dumps(store))

            #copy media files
            if os.path.exists(mediaSrcPath):
                for t in tracklist:
                    for m in glob.glob(mediaSrcPath+t+'.*'):
                        shutil.copy2(m,mediaPath)


if __name__ == '__main__':
    root = Tk()
    root.title("ENVOMUSE交付工具")
    root.minsize(825,700)
    root.geometry("825x700")

    root.rowconfigure(0,weight=1)
    root.columnconfigure(0,weight=1)

    eva = EnvoMaster(root,conn=DBConn())

    root.mainloop()