# -*- coding: utf-8 -*-
#
__author__ = 'jun'

from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from PIL import Image, ImageTk
import logging
import validators
import requests
import json
from db import DBConn
from sync import Sync
from main import EnvoMaster

class MainApp(Tk):
    def __init__(self,conn=None,session=None, *args,**kwargs):
        Tk.__init__(self,*args,**kwargs)

        self.serverAddr = 'http://localhost:9000'
        self.localMediaCachePath = '../media/'
        self.localExportPath = '../delivery/'

        self.session = session
        self.db_conn = conn
        self.logo = ImageTk.PhotoImage(Image.open('./logo.jpeg'))
        self.programSyncTotal = 0
        self.storeSyncTotal = 0
        self.mediaSyncTotal = 0
        self.programSyncProgress = 0
        self.storeSyncProgress = 0
        self.mediaSyncProgress = 0

        #define top layer frame
        self.container = Frame(self)
        self.container.pack(fill=BOTH,expand=True)
        # self.container.grid(column=0,row=1,sticky="nwes")
        # self.container.grid_rowconfigure(0, weight=1)
        # self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}    #frames

        for F in (EnvoAuth, SyncFrame, EnvoMaster):
            frame = F(self.container,self,self.db_conn)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(EnvoAuth)

    def show_frame(self,f):
        frame = self.frames[f]
        frame.tkraise()
        frame.onShow()

    def get_container(self):
        return self.container

    def get_conn(self):
        return self.db_conn

    def get_session(self):
        return self.session

    def set_srvAddr(self,s):
        self.serverAddr = s

    def get_srvAddr(self):
        return self.serverAddr

    def get_logo(self):
        return self.logo

    def get_programTotal(self):
        return self.programSyncTotal

    def set_programTotal(self,n):
        self.programSyncTotal = n

    def get_storeTotal(self):
        return self.programSyncTotal

    def set_storeTotal(self,n):
        self.programSyncTotal = n

    def get_mediaTotal(self):
        return self.programSyncTotal

    def set_mediaTotal(self,n):
        self.programSyncTotal = n

class EnvoAuth(Frame):
    def __init__(self,master=None,controller=None,conn=None):
        Frame.__init__(self,master)
        # self.grid(column=0,row=0,sticky="NWSE")
        self.pack(expand=True,fill=BOTH)

        self.controller = controller

        self.logo = self.controller.get_logo()
        self.username = StringVar()
        self.password = StringVar()
        self.srvaddr = StringVar()

    def onShow(self):
        banner = Frame(self)
        banner.grid(row=0,column=0,sticky="NWSE")
        self.label = Label(banner,image=self.logo)
        self.label.image = self.logo
        self.label.pack()

        body = Frame(self)
        body.grid(row=1,column=0,sticky="NSWE")
        Label(body,text="服务器地址：").grid(row=0,column=0,sticky="E")
        Entry(body,textvariable=self.srvaddr).grid(row=0,column=1)
        Label(body,text="用户名：").grid(row=1,column=0,sticky="E")
        Entry(body,textvariable=self.username).grid(row=1,column=1)
        Label(body,text="密码：").grid(row=2,column=0,sticky="E")
        Entry(body,show="*",textvariable=self.password).grid(row=2,column=1)

        Button(body,text="登陆",command=self.auth).grid(row=4,column=1,sticky=(W,E))

    def auth(self):
        testserver = "http://localhost:9000"

        try:
            url = self.srvaddr.get()
            if len(url.strip())==0:
                self.srvaddr.set(testserver)
                url = self.srvaddr.get()

            if url[-1] == "/":
                url=url[:-1]

            self.controller.set_srvAddr(url)

            usr = self.username.get()
            pwd = self.password.get()
            session = self.controller.get_session()

            if not validators.url(url.strip()) and url != testserver:
                messagebox.showwarning(title="错误",message="请检查服务器地址 "+url)
            elif usr.strip()=="" or pwd.strip()=="":
                messagebox.showwarning(title="错误",message="请检查用户名或密码")
            else:
                payload = {"email":usr,"password":pwd}
                r = session.post(url+'/login',data=payload)
                r.encoding='utf-8'
                if r.text=="Unauthorized":
                    messagebox.showerror(title="登录失败",message="登录失败")
                else:
                    res = json.loads(r.text)
                    if "admin" in res["user"]["roles"]:
                        print("LOGIN SUCCESS....")
                        self.controller.show_frame(SyncFrame)
                    else:
                        messagebox.showerror(title="登录失败",message="登录失败")
                # print(r.text)
                # payload = {"email":usr,"password":pwd}
                # r = requests.post(url+'/login',data=payload)
                # r.encoding='utf-8'
                # if r.text=="Unauthorized":
                #     messagebox.showerror(title="登录失败",message="登录失败")
                # else:
                #     res = json.loads(r.text)
                #     if "admin" in res["user"]["roles"]:
                #         print("LOGIN SUCCESS....")
                #         self.controller.show_frame(SyncFrame)
                #     else:
                #         messagebox.showerror(title="登录失败",message="登录失败")
        except Exception as e:
            print(e)

class SyncFrame(Frame):
    def __init__(self,master=None,controller=None,conn=None):
        Frame.__init__(self,master)

        self.controller = controller
        self.conn = self.controller.get_conn()
        self.logo = self.controller.get_logo()

        self.remotePgmTotal = 0
        self.remoteTrackTotal = 0

    def onShow(self):

        print(self.controller.get_srvAddr())
        self.sync = Sync(srvAddr=self.controller.get_srvAddr(),conn=self.conn,session=self.controller.get_session())

        if self.sync is not None:
            self.sync.dosync()
            self.remotePgmTotal = self.sync.getRemoteProgramTotalCount()
            self.remoteTrackTotal = self.sync.getRemoteTrackTotalCount()

        banner = Frame(self)
        banner.grid(row=0,column=0,sticky="WE")
        self.label = Label(banner,image=self.logo)
        self.label.image = self.logo
        self.label.pack()

        body = Frame(self)
        body.grid(row=1,column=0,sticky="NSWE")

        Label(body,text="歌曲同步中...",padding=(10, 5, 10, 5)).grid(row=1,column=0,sticky="WE")
        self.pgb_media = Progressbar(body, orient="horizontal", length=200, mode="determinate")
        self.pgb_media.grid(row=1,column=1,sticky="WE")
        self.pgb_media["value"]=0
        self.pgb_media["maximum"]=self.remoteTrackTotal

        self.sync.start()
        self.checkstatus()

    def checkstatus(self):
        self.pgb_media["value"] = 0 if self.sync is None else self.sync.getTrackIdx()
        if self.pgb_media["value"] >= self.remoteTrackTotal:
            self.gotoMain()
        else:
            self.after(200,self.checkstatus)

    def gotoMain(self):
        print('going to main....')
        self.controller.show_frame(EnvoMaster)

def main():
    '''
    Application main entry point
    '''
    logger = logging.Logger('mainApp')
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler('envo.log')
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.info('ENVOMUSE DELIVERY TOOL STARTED')

    db_conn = DBConn()
    db_conn.check() #prepare database

    app=MainApp(conn=db_conn,session=requests.session())
    app.title("ENVOMUSE交付工具")
    app.minsize(825,600)
    app.geometry("825x600")
    app.configure(background="white")
    app.rowconfigure(0,weight=1)
    app.columnconfigure(0,weight=1)

    app.mainloop()

if __name__ == '__main__':
    main()