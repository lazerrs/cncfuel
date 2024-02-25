#cnc fuel
import sys
from PyQt5.QtWidgets import QApplication,QGraphicsView,QComboBox,QLineEdit, QWidget, QPushButton, QVBoxLayout ,QGridLayout, QLabel, QTextEdit,QProgressBar
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5 import QtCore
import serial
import json
from time import sleep
from datetime import datetime
from ina219 import INA219
import adafruit_ds3231

import pandas as pd
from fpdf import FPDF, Template
import sqlite3
import pdfkit
from ina219 import DeviceRangeError

class fuel_sensor_TesterApp(QWidget):
	def __init__(self):
		super().__init__()
		
		#self.insert_data()
		self.rtc = adafruit_ds3231.DS3231(self.i2c)
		self.time_data = datetime.now()
		self.dtime = self.time_data.strftime('%Y%m%d%H%I%s')
		config = self.read_conf()
		self.rule_size = config['rule_size']
		self.moving_resolution = config['moving_resolution']
		self.pulse_for_free_rotation = config['pulse_for_free_rotation']
		self.steps = config['steps']
		self.number_of_steps = len(self.steps)
		self.delay_of_steps = config['delay_of_steps']
		self.sens_height_opt = config['sensor_heights']
		self.default_sensor_height = config['default_sensor_height']
		self.pulsedelay = config['pulsedelay'] #float(pulsedelay)
		self.go_to_zero_pulsedelay = config['go_to_zero_pulsedelay'] #float(pulsedelay)
		self.initdelay = config['initdelay']
		self.pulse2mm = config['pulse2mm']
		self.zero_high =config["zero_high" ]
		self.pulse_in_steps =0
		self.location=0
		self.box_command=0
		self.box_volt=0
		self.box_amper=0
		self.box_code=0
		self.box_data=0
		self.zero=False
		self.ser = serial.Serial ("/dev/ttyS0", 9600,timeout=2)
		self.setWindowTitle('KSA Fuel Sensor Tester')
		self.setWindowIcon(QIcon('/image/KASA-black-small.png'))
		self.setGeometry(0, 0, 800, 600)
		self.showFullScreen()
		layout = QGridLayout()
		layout.setGeometry(QtCore.QRect(100, 0, 505, 50))
		self.btn_exit = QPushButton('exit', self)
		#self.btn_exit.setGeometry(QtCore.QRect(100, 0, 505, 50))
		self.btn_exit.clicked.connect(self.exit_app)
		layout.addWidget(self.btn_exit,9,3)

		self.btn_send_message = QPushButton('go to sensor', self)
		self.btn_send_message.clicked.connect(self.send_message)
		layout.addWidget(self.btn_send_message,5,3)
		
		self.btn_zero = QPushButton('zero', self)
		self.btn_zero.clicked.connect(self.go_to_ref)
		layout.addWidget(self.btn_zero,4,3)
		
		self.btn_start_progress = QPushButton('start progress', self)
		self.btn_start_progress.clicked.connect(self.start_progress)
		layout.addWidget(self.btn_start_progress,6,3)
		self.btn_create_pdf = QPushButton('Create PDF', self)
		self.btn_create_pdf.clicked.connect(self.printed)
		layout.addWidget(self.btn_create_pdf,7,3)
		self.ex_label = QLabel("exam by:")
		self.sn_label = QLabel("serial number:")
		self.lineEdit_ex= QLineEdit(self)
		self.lineEdit_sn= QLineEdit(self)
		layout.addWidget(self.lineEdit_ex,0,3)
		layout.addWidget(self.ex_label,0,2)
		layout.addWidget(self.lineEdit_sn,1,3)
		layout.addWidget(self.sn_label,1,2)
		self.textbox = QTextEdit(self)
		
		self.btn_auto_progress = QPushButton('Auto progress', self)
		self.btn_auto_progress.clicked.connect(self.auto_progress)
		layout.addWidget(self.btn_send_message,2,3)
		self.textbox.setReadOnly(True)
		layout.addWidget(self.textbox,8,3)
		layout.addWidget(self.btn_auto_progress,3,3)
		self.combo_box = QComboBox(self)
		
		self.pbar=QProgressBar(self)
		self.pbar.setValue(0)
		layout.addWidget(self.pbar,10,2)
		self.graphicsView = QLabel()
		self.graphicsView.setObjectName(u"graphicsView")
		self.graphicsView.setGeometry(QtCore.QRect(540, 360, 71, 61))
		self.graphicsView.setPixmap(QPixmap('image/KASA-black-small.png'))
		layout.addWidget(self.graphicsView,1,1)
		for i in self.sens_height_opt :
			self.combo_box.addItem(i)
		layout.addWidget(self.combo_box,2,3)
		self.setLayout(layout)
		#while True :
		#	self.read_volt()
	
	def avrege_volt(self):
		out=0
		for i in range(10):
			a=self.read_ina()
			while a <=0:
				a=self.read_ina()
			out=round(out+a,3)
		return (out/10)
	def read_ina(self):
		SHUNT_OHMS = 0.1
		ina = INA219(SHUNT_OHMS)
		ina.configure()

		print("Bus Voltage: %.3f V" % ina.voltage())
		try:
			print("Bus Current: %.3f mA" % ina.current())
			print("Power: %.3f mW" % ina.power())
			print("Shunt voltage: %.3f mV" % ina.shunt_voltage())
			return ina.voltage()
		except DeviceRangeError as e:
			# Current out of device range with specified shunt resistor
			print(e)

	def read_ina12(self):
		SHUNT_OHMS = 0.1
		ina = INA219(SHUNT_OHMS,3,1,0x4c)
		ina.configure()
		
		print("Bus Voltage: %.3f V" % ina.voltage())
		try:
			print("Bus Current: %.3f mA" % ina.current())
			print("Power: %.3f mW" % ina.power())
			print("Shunt voltage: %.3f mV" % ina.shunt_voltage())
			return ina.voltage(),ina.current()
		except DeviceRangeError as e:
			# Current out of device range with specified shunt resistor
			print(e)
	def read_conf(self):
		f = open('config.json', "r")
		conf = json.loads(f.read())
		f.close()
		return conf
	def exit_app(self):
		QApplication.quit()
	def send_serial(self,data):
		print(str.encode("ks"+data+"ks"))
		self.ser.write(str.encode("ks"+data+"ks"))
	
        
	def insert_data(self,ins=0,time=0,sn=0,ex=0,model=0,testmethod=0,volt=0,amper=0,sensor_hi=0,rnd=0,kod=0,step=0,hight=0,validation=0,volt2=0):

        # import the mysql client for python

        # Create a connection object
        # IP address of the MySQL database server
		Host = "ksafuel.db"

		# User name of the database server
		User = "root"	

		# Password for the database user
		Password = '123'		

		conn = sqlite3.connect(Host)

		# Create a cursor object
		cur = conn.cursor()

		#creating database
		#cur.execute("CREATE DATABASE ksafuel.db")
		#cur.execute("CREATE table inde(id integer primary key autoincrement not null,time varchar(20)  not null ,sn int  not null,ex varchar(20)  not null,model varchar(20)  not null ,testmethod varchar(20)  not null,volt int  not null,amper int  not null,sensor_hi int  not null,rnd int  not null)")

		#cur.execute("CREATE table data(id integer primary key autoincrement not null,time varchar(20)  not null ,kod int  not null,step int  not null,hight int  not null,validation int  not null,volt int  not null)")
		if ins=="index":
			a="insert into inde(time,sn,ex,model,testmethod,volt,amper,sensor_hi,rnd)values('"+time+"'"+",'"+str(sn)+"','"+str(ex)+"'"+",'"+str(model)+"'"+",'"+testmethod+"',"+str(volt)+","+str(amper)+","+str(sensor_hi)+","+str(rnd)+")"
			print(a)
			cur.execute(a)
			cur.execute("select max(id) from inde ")
			res1 = cur.fetchall()
			for ress in res1:
				out=ress[(0)]
				
		if ins=="data":
			cur.execute("insert into data(kod,time,step,hight,validation,volt)values("+str(kod)+",'"+time+"',"+str(step)+","+str(hight)+","+str(validation)+","+str(volt2)+")")
			out="ok" 
		conn.commit()
		conn.close()
		return out
	def report_data(self,kod=114):

		# import the mysql client for python

		# Create a connection object
		# IP address of the MySQL database server
		Host = "ksafuel.db"

		# User name of the database server
		User = "root"	

		# Password for the database user
		Password = '123'		

		conn = sqlite3.connect(Host)

		# Create a cursor object
		cur = conn.cursor()
		cur.execute("select * from inde where id="+str(kod))

		res_index = cur.fetchall()
		cur.execute("select * from data where kod="+str(kod))
		res_data = cur.fetchall()


		df_index=pd.DataFrame(res_index,columns=['id','time', 'sn','ex', 'model','testmethod','volt','amper','sensor_hi','rnd'])
		df_data=pd.DataFrame(res_data,columns=['id','time','kod','step','hight','validation','volt'])

		a="""

		<!DOCTYPE html>
		<html>
		<head>
		<style>
		img {
		  width: 100%;
		}
		</style>
		</head>
		<body>

		<img src="./image/KASA-black-small.png" alt="HTML5 Icon" width="10" height="200" style="width:100px;height:100px;">



		</body>
		</html>
		"""+df_index.to_html()+df_data.to_html()
		f = open("11.html", "w")
		f.write(a)
		f.close()

		options = {
			'page-size': 'A4',
			'margin-top': '0.75in',
			'margin-right': '0.75in',
			'margin-bottom': '0.75in',
			'margin-left': '0.75in',
			'enable-local-file-access': None,
			'images':None,
		}

		#pdfkit.from_file('11.html', 'micro.pdf',options=options)  
		self.pdfed(df_index,df_data)          
	def pdfed(self,index1,data1):
        # save FPDF() class into a
        # variable pdf
        # pdf = FPDF()
		print(data1)
		#current_datetime = self.time_data.strftime('%Y%m%d%H%I%s')
		current_datetime = index1.iloc[0,1]
		sn=index1.iloc[0,2]
		self.exam_by=index1.iloc[0,3]
		sensor_h=str(index1.iloc[0,8])+"  mm"
		
		#this will define the ELEMENTS that will compose the template. 
		elements = [
			{ 'name': 'company_logo', 'type': 'I', 'x1': 20.0, 'y1': 20.0, 'x2': 35.0, 'y2': 35.0, 'font': None, 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'logo', 'priority': 2, },
			{ 'name': 'company_name1', 'type': 'T', 'x1': 35.0, 'y1': 25, 'x2': 50.0, 'y2': 30, 'font': 'Arial', 'size': 12.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': '', 'priority': 2, },
			{ 'name': 'company_name2', 'type': 'T', 'x1': 35.0, 'y1': 30, 'x2': 50.0, 'y2': 35, 'font': 'Arial', 'size': 6.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': '', 'priority': 2, },
			{ 'name': 'box', 'type': 'B', 'x1': 10.0, 'y1': 10.0, 'x2': 140.0, 'y2': 200.0, 'font': 'Arial', 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background':0xFFFFFF, 'align': 'l', 'text': None, 'priority': 0, },
			{ 'name': 'line1', 'type': 'L', 'x1': 20.0, 'y1': 37.0, 'x2': 130.0, 'y2': 37.0, 'font': 'Arial', 'size': 0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': None, 'priority': 3, },
			{ 'name': 'barcode_serial', 'type': 'T', 'x1': 100.0, 'y1': 20, 'x2': 130.0, 'y2': 25.0, 'font': 'Arial', 'size': 6.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'r', 'text': current_datetime, 'priority': 2, },
			{ 'name': 'barcode', 'type': 'BC', 'x1': 80.0, 'y1': 25, 'x2': 130.0, 'y2': 35.0, 'font': 'Interleaved 2of5 NT', 'size': 0.75, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'r', 'text': current_datetime, 'priority': 3, },
			{ 'name': 'date_label', 'type': 'T', 'x1': 20.0, 'y1': 45, 'x2': 60.0, 'y2': 50.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': 'Date :', 'priority': 2, },
			{ 'name': 'date_value', 'type': 'T', 'x1': 60.0, 'y1': 45, 'x2': 90.0, 'y2': 50.0, 'font': 'Arial', 'size': 6.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': current_datetime, 'priority': 2, },
			{ 'name': 'exp_by_label', 'type': 'T', 'x1': 20.0, 'y1': 50, 'x2': 60.0, 'y2': 55.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Experiment by :', 'priority': 2, },
			{ 'name': 'exp_by_value', 'type': 'T', 'x1': 60.0, 'y1': 50, 'x2': 90.0, 'y2': 55.0, 'font': 'Arial', 'size': 6.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': self.exam_by, 'priority': 2, },
			{ 'name': 'sense_height_label', 'type': 'T', 'x1': 20.0, 'y1': 60, 'x2': 60.0, 'y2': 65.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Sensor height :', 'priority': 2, },
			{ 'name': 'sense_height_value', 'type': 'T', 'x1': 60.0, 'y1': 60, 'x2': 90.0, 'y2': 65.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': str(sensor_h), 'priority': 2, },
			
			{ 'name': 'date_label', 'type': 'T', 'x1': 20.0, 'y1': 45, 'x2': 60.0, 'y2': 50.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Date :', 'priority': 2, },
			{ 'name': 'date_value', 'type': 'T', 'x1': 60.0, 'y1': 45, 'x2': 90.0, 'y2': 50.0, 'font': 'Arial', 'size': 6.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': current_datetime, 'priority': 2, },
			
			{ 'name': 'sense_label', 'type': 'T', 'x1': 20.0, 'y1': 55, 'x2': 60.0, 'y2': 60.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Serial number :', 'priority': 2, },
			{ 'name': 'sense_label', 'type': 'T', 'x1': 60.0, 'y1': 55, 'x2': 60.0, 'y2': 60.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': str(sn) +"			" +str(index1.iloc[0,0]) , 'priority': 2, },
			
			{ 'name': 'volt_label', 'type': 'T', 'x1': 20.0, 'y1': 65, 'x2': 60.0, 'y2': 70.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'voltage :'+str(index1.iloc[0,6])+"  volt", 'priority': 2, },
			{ 'name': 'amper_ label', 'type': 'T', 'x1': 60.0, 'y1': 65, 'x2': 60.0, 'y2': 70.0, 'font': 'Arial', 'size': 6.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': "amper : " +str(round(index1.iloc[0,7]))+"  mAmper" , 'priority': 2, },
			
			{ 'name': 'details_header', 'type': 'T', 'x1': 20.0, 'y1': 70, 'x2': 90.0, 'y2': 75.0, 'font': 'Arial', 'size': 12.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Test Details', 'priority': 2, },
			{ 'name': 'line2', 'type': 'L', 'x1': 20.0, 'y1': 80.0, 'x2': 130.0, 'y2': 80.0, 'font': 'Arial', 'size': 0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': None, 'priority': 3, },


		]

		elements.append({ 'name': 'step_index', 'type': 'T', 'x1': 20.0, 'y1': 75, 'x2': 60.0, 'y2': 80,      'font': 'Arial', 'size': 9.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'STEP', 'priority': 2, })
		elements.append({ 'name': 'Direction', 'type': 'T', 'x1': 35.0, 'y1': 75, 'x2': 85.0, 'y2': 80,       'font': 'Arial', 'size': 9.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'locatin', 'priority': 2, })
		# elements.append({ 'name': 'Tolerance', 'type': 'T', 'x1': 85.0, 'y1': 75, 'x2': 105.0, 'y2': 80,      'font': 'Arial', 'size': 9.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': 'Tolerance', 'priority': 2, })
		elements.append({ 'name': 'Voltage', 'type': 'T', 'x1': 50.0, 'y1': 75, 'x2': 105.0, 'y2': 80,      'font': 'Arial', 'size': 9.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Voltage', 'priority': 2, })
		elements.append({ 'name': 'Validation', 'type': 'T', 'x1': 70.0, 'y1': 75, 'x2': 125.0, 'y2': 80,    'font': 'Arial', 'size': 9.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Validation', 'priority': 2, })
		elements.append({ 'name': 'Real Telorance', 'type': 'T', 'x1': 90.0, 'y1': 75, 'x2': 125.0, 'y2': 80,'font': 'Arial', 'size': 9.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Real Telorance', 'priority': 2, })
		elements.append({ 'name': 'Validated', 'type': 'T', 'x1': 115.0, 'y1': 75, 'x2': 135.0, 'y2': 80,      'font': 'Arial', 'size':9.0,'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l','text': 'Validated', 'priority': 2, })

		i = 0
		for step_index,row  in data1.iterrows():
			#step_index=125
			
			i = i+1
			yn = (i*5)+75
			elements.append({ 'name': 'step_index'+str(step_index), 'type': 'T', 'x1': 20.0, 'y1': yn, 'x2': 60.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': str(data1.iloc[step_index,3]), 'priority': 2, })
			elements.append({ 'name': 'Direction'+str(step_index), 'type': 'T', 'x1': 35.0, 'y1': yn, 'x2': 85.0, 'y2': yn+8,       'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': str(data1.iloc[step_index,4]), 'priority': 2, })
			# elements.append({ 'name': 'Tolerance'+str(step_index), 'type': 'T', 'x1': 85.0, 'y1': yn, 'x2': 105.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'I', 'text': str(self.report[chan_index][step_index]['Tolerance']), 'priority': 2, })
			elements.append({ 'name': 'Voltage'+str(step_index), 'type': 'T', 'x1': 50.0, 'y1': yn, 'x2': 105.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text':str(round(data1.iloc[step_index,6])), 'priority': 2, })
			elements.append({ 'name': 'Validation'+str(step_index), 'type': 'T', 'x1': 70.0, 'y1': yn, 'x2': 125.0, 'y2': yn+8,    'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': str(str(data1.iloc[step_index,5])) + ' +- 50', 'priority': 2, })
			elements.append({ 'name': 'Real Telorance'+str(step_index), 'type': 'T', 'x1': 90.0, 'y1': yn, 'x2': 125.0, 'y2': yn+8,'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': self.set_sensor_tolerance(round(data1.iloc[step_index,6]) ,data1.iloc[step_index,5]), 'priority': 2, })
			elements.append({ 'name': 'Validated'+str(step_index), 'type': 'T', 'x1': 115.0, 'y1': yn, 'x2': 135.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': self.set_sensor_validate(data1.iloc[step_index,6] ,data1.iloc[step_index,5]), 'priority': 2, })
			
			#elements.append({ 'name': 'step_index'+str(step_index), 'type': 'T', 'x1': 20.0, 'y1': yn, 'x2': 60.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': str(step_index), 'priority': 2, })
			#elements.append({ 'name': 'Direction'+str(step_index), 'type': 'T', 'x1': 45.0, 'y1': yn, 'x2': 85.0, 'y2': yn+8,       'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Direction', 'priority': 2, })
			# elements.append({ 'name': 'Tolerance'+str(step_index), 'type': 'T', 'x1': 85.0, 'y1': yn, 'x2': 105.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'c', 'text': str(self.report[chan_index][step_index]['Tolerance']), 'priority': 2, })
			#elements.append({ 'name': 'Voltage'+str(step_index), 'type': 'T', 'x1': 65.0, 'y1': yn, 'x2': 105.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Voltage', 'priority': 2, })
			#elements.append({ 'name': 'Validation'+str(step_index), 'type': 'T', 'x1': 85.0, 'y1': yn, 'x2': 125.0, 'y2': yn+8,    'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Validation' + ' +- 0.05', 'priority': 2, })
			#elements.append({ 'name': 'Real Telorance'+str(step_index), 'type': 'T', 'x1': 105.0, 'y1': yn, 'x2': 145.0, 'y2': yn+8,'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text': 'Real Telorance', 'priority': 2, })
			#elements.append({ 'name': 'Validated'+str(step_index), 'type': 'T', 'x1': 125.0, 'y1': yn, 'x2': 175.0, 'y2': yn+8,      'font': 'Arial', 'size': 8.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0xFFFFFF, 'align': 'l', 'text':'Validated', 'priority': 2, })644

			
		#here we instantiate the template and define the HEADER
		f = Template(format="A5", elements=elements, title="  fuel sensor report")
		f.add_page()

		#we FILL some of the fields of the template with the information we want
		#note we access the elements treating the template instance as a "dict"
		f["company_name1"] = "K . S . A"
		f["company_name2"] = "Kavoshgaran Sepehr Alborz"
		f["company_logo"] = "KASA-black-small.png"
		f["sense_height_value"] = sensor_h

		#and now we render the page
		#f.render("pdf/"+current_datetime+str(chan_index)+".pdf")
		#self.printed("pdf/"+current_datetime+str(chan_index)+".pdf")    
		f.render("pdf/"+str(sn)+"-"+str(index1.iloc[0,0])+".pdf")
		#self.printed("pdf/11.pdf")
	def printed(self, file="pdf/11.pdf"):
		self.report_data(113)
		conn = cups.Connection()
		printers = conn.getPrinters()
		printer_name = list(printers.keys())[0]
		conn.printFile(printer_name,"pdf/11.pdf","",{})        
				
	def go_to_ref(self):    
		if self.chek_conection() :
			zero = bytes('kszeroo', "utf-8") +str.encode("u")+str.encode("zeroo")+str.encode("u")+str.encode('zse')
			recived_data = self.send_resive(zero)
			st="zero" in recived_data
			print(recived_data , "zero", st)
			while not st:
				recived_data = self.resive()
				st="zero" in recived_data
				print(recived_data , "zero", st)
			self.start_pomp(500,"u",0)

			self.location=self.zero_high
			self.zero=(True)
			self.textbox.append("zero"+str(self.location))
	def go_to_sensor(self):    
			if self.chek_conection() :
				sensor_height2=str(self.combo_box.currentText())
				print(sensor_height2)
				sensor_height = float(sensor_height2.replace(' mm', ''))
				hi=self.location-sensor_height
				if hi>0 :dir1="u"
				if hi<0 : dir1="d"
				if hi==0 :dir1="z"
				self.rotate4(int(abs(hi)*self.pulse2mm),dir1,hi) 
				self.start_pomp(int(abs(hi)*self.pulse2mm),dir1,hi)
				self.read_volt()
	
	def set_sensor_validation(self,volt ,step_id):
		step_info = self.steps[step_id]
		real_distance = round(volt, 3) - step_info['validation_value']
		if abs(real_distance) > step_info['validation_tolerance'] :
		   
			validation = 0
		else:
			validation = 1
		   

		return round(step_info['validation_value']*1000 )
		
	def set_sensor_validate(self,volt ,tol):
		
		real_distance = round(volt, 3) - tol
		if abs(real_distance) > 50:
		   
			validation =  "Fail"
		else:
			validation ="OK"
		   

		return validation
	def set_sensor_tolerance(self,volt ,tol):
		
		real_distance = round(volt, 3) - tol
		validation =  str(real_distance)
		
		   

		return validation		
	def auto_progress(self):
		if not self.zero:
			self.go_to_ref()
		self.go_to_sensor()
		sleep(5)
		self.start_progress()
		
		
		
		
		
		
	def start_progress(self):  
			self.pbar.setValue(0)
			sensor_height2=str(self.combo_box.currentText())
			sensor_height =int(sensor_height2.replace(' mm', ''))
			a=self.insert_data("index",self.dtime,self.lineEdit_sn.text(),self.lineEdit_ex.text(),sensor_height2,"quick",self.read_ina12()[0],self.read_ina12()[1],sensor_height)
			self.textbox.append(" sensor voltage : "+str(self.read_ina12()[0]) +"	Volt	"+" sensor Amper : "+str(round(self.read_ina12()[1],2))+ "	mA")
			step=0
			volt=0
			
			sensor_height2=str(self.combo_box.currentText())
			self.calc_steps_new(sensor_height2)
			sensor_height = float(sensor_height2.replace(' mm', ''))-28
			hi=11.5
			
			
			if self.chek_conection() :
				
				self.rotate4(int(11.5*self.pulse2mm ),"u",hi) 
				self.start_pomp(int(11.5*self.pulse2mm ),"u",hi)
				
				
				sleep(10)
				volt=(self.avrege_volt()*1000)
				self.textbox.append(" step 0 :	"+ str(round(volt)) +"	mVolt")
				self.insert_data("data",self.dtime,1,0,0,0,0,0,0,0,a,step,round(self.location,2),self.set_sensor_validation(3 ,0),volt)
				hi=sensor_height/10
				
				for i in range( 10) :
					step=step+1
					self.rotate4(self.pulse_in_steps ,"u",hi) 			
					self.start_pomp(self.pulse_in_steps,"u",hi)
					sleep(20)
					volt=(self.avrege_volt()*1000)
					self.textbox.append(" step " +str(step)+"	"+str(round(volt))+ "	mVolt" )
					self.insert_data("data",self.dtime,1,0,0,0,0,0,0,0,a,step,round(self.location,2),self.set_sensor_validation(3 ,step),volt)
					self.pbar.setValue(step*5)
				for i in range (10):
					step=step+1
					self.rotate4(self.pulse_in_steps ,"d",hi) 			
					#self.start_pomp(self.pulse_in_steps*2,"d",hi)
					sleep(20)
					volt=(self.avrege_volt()*1000)
					self.textbox.append(" step " +str(step)+"	"+str(round(volt))+ "	mVolt" )
					self.insert_data("data",self.dtime,1,0,0,0,0,0,0,0,a,step,round(self.location,2),self.set_sensor_validation(3 ,9-i),volt)
					self.pbar.setValue(step*5)	
			hi=11.5
			self.rotate4(int(11.5*self.pulse2mm ),"d",hi) 
			self.report_data(a)
			
			
			
			
			
			
			
	def calc_steps_new(self, sensor_height):

		steps = self.number_of_steps
		delay = self.delay_of_steps

		sensor_height = float(sensor_height.replace(' mm', ''))-28

		self.pulse_in_steps = int(self.pulse2mm * ((sensor_height) / (steps-1)))

		
        
        
	def s(self):    
			if self.chek_conection() :
				sensor_height2=str(self.combo_box.currentText())
				print(sensor_height2)
				sensor_height = float(sensor_height2.replace(' mm', ''))
				hi=self.location-sensor_height
				if hi>0 :dir1="u"
				if hi<0 : dir1="d"
				if hi==0 :dir1="z"
				self.rotate4(int(abs(hi)*self.pulse2mm),dir1,hi) 				
				
						
			 
	def send_resive (self, send_data):
		ser = serial.Serial ("/dev/ttyS0",9600, timeout=1)
		ser.write(send_data)
		
		print(str(send_data)+"hi")
		sleep(.1)
		received_data = ser.read()
		sleep(.1)
		data_left = ser.inWaiting() #check for remaining byte
		received_data += ser.read(data_left)
		recived_data1 = (str(received_data))
		print(recived_data1)
		return recived_data1
	def send_resive1 (self, send_data):
		ser = serial.Serial ("/dev/ttyS0",9600)
		print(str(send_data)+"hi")
		ser.write(send_data)
		
		sleep(.1)
		received_data = ser.read()
		sleep(.1)
		data_left = ser.inWaiting() #check for remaining byte
		received_data += ser.read(data_left)
		recived_data1 = (str(received_data))
		print(recived_data1)
		return recived_data1
	def resive (self):
		ser = serial.Serial ("/dev/ttyS0",9600,timeout=2)
		
		received_data = ser.read()
		sleep(.1)
		data_left = ser.inWaiting() #check for remaining byte
		received_data += ser.read(data_left)
		recived_data1 = (str(received_data))
		print(recived_data1)
		return recived_data1
	def chek_conection (self):
		print("Hiiii")
		con_st=False
		for i in range (10) :
			if con_st:
				break
		
			hi = bytes('kshiiii', "utf-8") +str.encode("u")+str.encode("2iiii")+str.encode("u")+str.encode('sm')
			resive=self.send_resive1(hi)
			con_st=("hiras")in resive
			print("a",resive,con_st)
		return con_st
	def read_volt(self):
		load='nok'  
		
		while load=='nok':    
			rotation_serial_m = bytes('ks' +"volt0uvolt0u", "utf-8")+str.encode('1ve')
			
			print (rotation_serial_m)
			#transmit data serially"
			
			recived_data1 = self.send_resive(rotation_serial_m)
			print(recived_data1)
			load='nok'
			for i in range(len(recived_data1)):
				print (len(recived_data1))
				if recived_data1[i]=='v' and recived_data1[i+1]=='o' and recived_data1[i+2]=='l':
					#self.textbox.append(recived_data1[i+4]+recived_data1[i+5]+recived_data1[i+6])
					load='ok'
					break
					
			if load == 'ok':
				#self.textbox.append("volt")		
				return True
			
	def start_pomp (self,pulse4,dir4,hi):
		load='nok'  
		rotate='nok'
		pulse3=str(round(pulse4/30)  )  
		if len(pulse3)<5:
				for i in range(5-len(pulse3)):
					pulse3 ='0'+ pulse3      
		while load=='nok':    
			rotation_serial_m = bytes('ks', "utf-8") +str.encode(pulse3)+str.encode(dir4)+str.encode(pulse3)+str.encode(dir4)+str.encode('1pe')
			
			print (rotation_serial_m)
			#transmit data serially"
			
			recived_data1 = self.send_resive(rotation_serial_m)
			print(recived_data1)
			load='nok'
			for i in range(len(recived_data1)):
				print (len(recived_data1))
				if recived_data1[i]=='s' and recived_data1[i+1]=='u' and recived_data1[i+2]=='c':
					#self.textbox.append("pomp start")
					load='ok'
					break
					
						
			if load == 'ok':
				   print(recived_data1+load)#read serial port
				   rotate='nok'
				   while rotate=='nok':
					   recived_data1 = self.resive()
					   for i in range(len (recived_data1)):
						   if recived_data1[i]=='t' and recived_data1[i+1]=='a' and  recived_data1[i+2]=='m':
							   rotate='ok'
							   print("ok")
							   break
			if rotate == 'ok':
				#self.textbox.append("pomp stop")		
				return True
			
	def rotate4 (self,pulse4,dir4,hi):
		if True:
			pulse=pulse4
			if 	pulse==0:return True
			self.jahat=dir4
			load='nok'
	 
			
			i4=1
			pulse3=(str(pulse))
			
			print(pulse)
			if len(pulse3)<5:
				for i in range(5-len(pulse3)):
					pulse3 ='0'+ pulse3
			if pulse>60000 :
				i4=int(pulse/60000)+1        
			for i in range(i4):
			
				print (i ,i4)
				if pulse>60000 :
					pulse3=str(60000)
				else:
					pulse3=str(pulse)
					if len(pulse3)<5:
						for i in range(5-len(pulse3)):
							pulse3 ='0'+ pulse3
				load='nok'            
				for j in range (10):
					if load=='nok':    
						rotation_serial_m = bytes('ks', "utf-8") +str.encode(pulse3)+str.encode(dir4)+str.encode(pulse3)+str.encode(dir4)+str.encode('1re')
						
						print (rotation_serial_m)
						#transmit data serially"
						
						recived_data1 = self.send_resive(rotation_serial_m)
						print(recived_data1)
						load='nok'
						for i in range(len(recived_data1)):
							print (len(recived_data1))
							if recived_data1[i]=='s' and recived_data1[i+1]=='u' and recived_data1[i+2]=='c':
							   load='ok'
							   break
						
						
				if load == 'ok':
				   print(recived_data1+load)#read serial port
				   rotate='nok'
				   
				while  rotate=='nok':
				   recived_data1 = self.resive()
				   for i in range(len (recived_data1)):
					   if recived_data1[i]=='t' and recived_data1[i+1]=='a' and  recived_data1[i+2]=='m':
						   rotate='ok'
						   print("ok")
						   break
				   if rotate == 'ok':
						   #print(str(received_data)+rotate)
						   pulse=pulse-60000
						   sleep(1)
					   
			if rotate == 'ok':  
				if dir4=="u":
					self.location=self.location-abs(hi)
				if dir4=="d":
					self.location=self.location+abs(hi)	
			self.textbox.append( "locatin :" + str(round(self.location))+"  mm")		
			return True
		else:
		   return False


	
	def read_box(self):
		
		#try: 
			 
			received_data = self.ser.read()
			
			time.sleep(.1)
			data_left = self.ser.inWaiting() #check for remaining byte
			received_data += self.ser.read(data_left)
			print (str(received_data)) #print received data
			recived_data1=str(received_data)
			a = len(str(received_data))
			print(recived_data1)
			
			
			for i in range(a):
				start=0
				end=0
				
				if recived_data1[i]=='k' and recived_data1[i+1]=='s' :
					start=i+2
					for i1 in range(a-i):
						
						if recived_data1[i1+i]=='k' and recived_data1[i1+i+1]=='e' :
							end=i1+i
							resive=json.loads(recived_data1[start:end])
							self.box_command=resive["command"]
							self.box_volt=resive["volt"]
							self.box_amper=resive["amper"]
							self.box_code=resive["code"]
							self.box_data=resive["data"]
							
							break   
					 
					break
				  
			#print(self.rpm,"rpm",self.temp)
			return "ok"
	#	except serial.SerialTimeoutException :
			print('not read')
	#	except:
			return "err"	
	def send_message(self):
		self.go_to_sensor()
		
		# Write code to send message via serial port and display response in textbox
	
	
		
	def add_text_box(self, text1):
		current_text=self.textbox.toPlainText()
		self.textbox.setPlainText(current_text+text1)
		
	def create_pdf(self):
		i = I2C(1, scl=Pin(3), sda=Pin(2),freq=20000)
		print("I2C Bus Scan: ", i.scan(), "\n")
		 
		sensor = ina219.INA219(i,64)
		sensor.set_calibration_16V_400mA()
 
		current_text=self.textbox.toPlainText()
		pdf = fpdf.FPDF(format='A5')
		pdf.add_page()
		pdf.set_font("Arial", size=12)
		pdf.cell(200, 10, current_text, ln=True)
		pdf.output("test.pdf")
	pass
if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = fuel_sensor_TesterApp()
	window.show()
	sys.exit(app.exec_())
