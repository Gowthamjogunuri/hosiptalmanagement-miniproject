from django.shortcuts import render
from django.conf import settings
import pymysql
from datetime import datetime
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import cv2
import numpy as np
import pytesseract
import os
import matplotlib.pyplot as plt
from ultralytics import YOLO
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = os.environ.get(
    "TESSERACT_CMD",
    "tesseract",
)


def connect_to_database():
    connection_options = {}
    ssl_ca = os.environ.get("MYSQL_SSL_CA")
    if ssl_ca:
        connection_options["ssl"] = {
            "ca": ssl_ca,
            "check_hostname": True,
        }

    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DATABASE", "redact"),
        charset="utf8",
        **connection_options,
    )


global username, disease, aadhar_data, aadhar_name, medical_data, medical_name
labels = ['Aadhar_no', 'DOB', 'Gender', 'Name']
#yolo confidence threshold to detect hand signs
CONFIDENCE_THRESHOLD = 0.50
GREEN = (0, 255, 0)
yolo_model = YOLO(str(settings.BASE_DIR / "model" / "best.pt"))
print("Yolo11 Model Loaded")

#function to detect aadhar card
def getAadharNo(frame):
    global yolo_model
    detections = yolo_model(frame)[0]
    label = None
    aadhar_no = ""
    for data in detections.boxes.data.tolist():
        confidence = data[4]
        cls_id = data[5]
        if float(confidence) >= CONFIDENCE_THRESHOLD:
            xmin, ymin, xmax, ymax = int(data[0]), int(data[1]), int(data[2]), int(data[3])
            label = labels[int(cls_id)]
            if label == 'Aadhar_no':
                region = frame[ymin:ymax, xmin:xmax]
                text = pytesseract.image_to_string(region)
                if len(text.strip()) > 0:
                    aadhar_no = text.strip()
                    break                       
    return aadhar_no

def maskAadhar(img):
    global yolo_model
    detections = yolo_model(img)[0]
    label = None
    for data in detections.boxes.data.tolist():
        confidence = data[4]
        cls_id = data[5]
        if float(confidence) >= CONFIDENCE_THRESHOLD:
            xmin, ymin, xmax, ymax = int(data[0]), int(data[1]), int(data[2]), int(data[3])            
            label = labels[int(cls_id)]
            if label == 'Aadhar_no':
                max_mask = xmin + int(xmax / 3)
                for y in range(ymin, ymax):
                    for x in range(xmin, max_mask):
                        img[y, x] = [0, 0, 0]    
            cv2.rectangle(img, (xmin, ymin) , (xmax, ymax), GREEN, 2)
            cv2.putText(img, label, (xmin, ymin-10),  cv2.FONT_HERSHEY_SIMPLEX,0.7, (255, 0, 0), 2)        
    return img

def ViewDoctors(request):
    if request.method == 'GET':
        global username
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Username</font></th>'
        output+='<th><font size=3 color=black>Password</font></th>'
        output+='<th><font size=3 color=black>Phone No</font></th>'
        output+='<th><font size=3 color=black>Email ID</font></th>'
        output+='<th><font size=3 color=black>Address</font></th>'
        output+='<th><font size=3 color=black>Description</font></th></tr>'
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select * from user_signup where usertype='Doctor'")
            lists = result.fetchall()
            for ls in lists:
                output+='<tr><td><font size=3 color=black>'+str(ls[0])+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[2]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[3]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[4]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[5]+'</font></td></tr>'
        context= {'data':output}        
        return render(request,'AdminScreen.html', context)

def ViewBillingAction(request):
    if request.method == 'POST':
        global username
        patient_name = request.POST.get('t1', False)
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Billing ID</font></th>'
        output+='<th><font size=3 color=black>Patient Name</font></th>'
        output+='<th><font size=3 color=black>Bill Amount</font></th>'
        output+='<th><font size=3 color=black>Bill Date</font></th>'
        output+='<th><font size=3 color=black>Bill Description</font></th></tr>'
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select * from billing where patient_name='"+patient_name+"'")
            lists = result.fetchall()
            for ls in lists:
                output+='<tr><td><font size=3 color=black>'+str(ls[0])+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[2]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[3]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[4]+'</font></td></tr>'
        context= {'data':output}        
        return render(request,'InsuranceScreen.html', context) 

def ViewBilling(request):
    if request.method == 'GET':
        return render(request, 'ViewBilling.html', {}) 

def confirmProfileAction(request):
    if request.method == 'POST':
        global username, disease, aadhar_data, aadhar_name, medical_data, medical_name
        today = str(datetime.now())
        aadhar_no = request.POST.get('t1', False)
        dbconnection = connect_to_database()
        dbcursor = dbconnection.cursor()
        qry = "INSERT INTO patients VALUES('"+str(username)+"','"+disease+"','"+aadhar_no+"','"+aadhar_name+"','"+medical_name+"','"+str(today)+"')"
        dbcursor.execute(qry)
        dbconnection.commit()
        if dbcursor.rowcount == 1:
            data = "Your profile successfully updated in Database"
            context= {'data':data}
            settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
            aadhar_path = settings.MEDIA_ROOT / Path(aadhar_name).name
            medical_path = settings.MEDIA_ROOT / Path(medical_name).name
            with open(aadhar_path, "wb") as file:
                file.write(aadhar_data)
            with open(medical_path, "wb") as file:
                file.write(medical_data)
            return render(request,'PatientScreen.html', context)
        else:
            data = "Error in saving your profile"
            context= {'data':data}
            return render(request,'PatientScreen.html', context)

def CreateProfileAction(request):
    if request.method == 'POST':
        global username, disease, aadhar_data, aadhar_name, medical_data, medical_name
        disease = request.POST.get('t1', False)
        aadhar_data = request.FILES['t2'].read()
        aadhar_name = request.FILES['t2'].name
        medical_data = request.FILES['t3'].read()
        medical_name = request.FILES['t3'].name
        img = cv2.imdecode(np.frombuffer(aadhar_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return render(request, 'CreateProfile.html', {
                'data': 'The uploaded Aadhaar image could not be read.'
            })
        img = cv2.resize(img, (500, 500))
        aadhar_no = getAadharNo(img)
        output = '<tr><td><font size="3" color="black">Detected&nbsp;Aadhar&nbsp;No</td><td><input type="text" name="t1" size="25" value="'+aadhar_no+'"/></td></tr>'
        context= {'data1':output}
        return render(request,'ConfirmProfile.html', context)        

def CreateProfile(request):
    if request.method == 'GET':
        return render(request, 'CreateProfile.html', {})  

def AppointmentAction(request):
    if request.method == 'POST':
        global username
        doctor = request.POST.get('t1', False)
        disease = request.POST.get('t2', False)
        date = request.POST.get('t3', False)
        today = str(datetime.now())
        bid = 0
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select max(appointment_id) from appointment")
            lists = result.fetchall()
            for ls in lists:
                bid = ls[0]
        if bid != None:
            bid = bid + 1
        else:
            bid = 1
        dbconnection = connect_to_database()
        dbcursor = dbconnection.cursor()
        qry = "INSERT INTO appointment(appointment_id,patient_name,doctor_name,disease_details,prescription,appointment_date,booking_date) VALUES('"+str(bid)+"','"+username+"','"+doctor+"','"+disease+"','Pending','"+date+"','"+str(today)+"')"
        dbcursor.execute(qry)
        dbconnection.commit()
        if dbcursor.rowcount == 1:
            data = "Your Appointment Confirmed on "+date
            context= {'data':data}
            return render(request,'PatientScreen.html', context)
        else:
            data = "Error in making appointment"
            context= {'data':data}
            return render(request,'PatientScreen.html', context)     
            

def Appointment(request):
    if request.method == 'GET':
        global doctor
        doctor = request.GET['doctor']
        output = '<tr><td><font size="3" color="black">Doctor</td><td><input type="text" name="t1" size="25" value="'+doctor+'" readonly/></td></tr>'
        context= {'data':output}
        return render(request,'BookAppointment.html', context)

def getDetails(user):
    address = ""
    email = ""
    phone = ""
    mysqlConnect = connect_to_database()
    with mysqlConnect:
        result = mysqlConnect.cursor()
        result.execute("select phone_no, email, address from user_signup where username='"+user+"'")
        lists = result.fetchall()
        for ls in lists:
            phone = ls[0]
            email = ls[1]
            address = ls[2]
    return phone, email, address        
    

def ViewPrescription(request):
    if request.method == 'GET':
        global username
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Appointment ID</font></th>'
        output+='<th><font size=3 color=black>Patient Name</font></th>'
        output+='<th><font size=3 color=black>Doctor Name</font></th>'
        output+='<th><font size=3 color=black>Disease Details</font></th>'
        output+='<th><font size=3 color=black>Prescription</font></th>'
        output+='<th><font size=3 color=black>Appointment Date</font></th>'
        output+='<th><font size=3 color=black>Booking Date</font></th></tr>'
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select * from appointment where patient_name='"+username+"'")
            lists = result.fetchall()
            for ls in lists:
                output+='<tr><td><font size=3 color=black>'+str(ls[0])+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[2]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[3]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[4]+'</font></td>'
                output+='<td><font size=3 color=black>'+str(ls[5])+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[6]+'</font></td></tr>'
        context= {'data':output}        
        return render(request,'PatientScreen.html', context) 

def GeneratePrescription(request):
    if request.method == 'GET':
        global username
        bid = request.GET['pid']
        output = '<tr><td><font size="3" color="black">Appointment&nbsp;ID</td><td><input type="text" name="t1" size="25" value="'+bid+'" readonly/></td></tr>'
        context= {'data':output}
        return render(request,'GeneratePrescription.html', context)

def saveBilling(aid):
    global username
    patient_name = ""
    mysqlConnect = connect_to_database()
    with mysqlConnect:
        result = mysqlConnect.cursor()
        result.execute("select patient_name from appointment where appointment_id='"+aid+"'")
        lists = result.fetchall()
        for ls in lists:
            patient_name = ls[0]
            break
    today = str(datetime.now())
    dbconnection = connect_to_database()
    dbcursor = dbconnection.cursor()
    qry = "INSERT INTO billing VALUES('"+str(aid)+"','"+patient_name+"','1000','"+today+"','Consultation with doctor "+username+"')"
    dbcursor.execute(qry)
    dbconnection.commit()      
    

def GeneratePrescriptionAction(request):
    if request.method == 'POST':
        bid = request.POST.get('t1', False)
        prescription = request.POST.get('t2', False)
        dbconnection = connect_to_database()
        dbcursor = dbconnection.cursor()
        qry = "update appointment set prescription='"+prescription+"' where appointment_id='"+bid+"'"
        dbcursor.execute(qry)
        dbconnection.commit()
        saveBilling(bid)
        if dbcursor.rowcount == 1:
            data = "Prescription Updated Successfully"
            context= {'data':data}
            return render(request,'DoctorScreen.html', context)
        else:
            data = "Error in adding prescription details"
            context= {'data':data}
            return render(request,'DoctorScreen.html', context)

def DownloadAction(request):
    if request.method == 'GET':
        global accessList, username
        name = request.GET.get('requester', False)
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select medical_img from patients where patient_name='"+name+"'")
            lists = result.fetchall()
            for ls in lists:
                name = ls[0]
                break
        with open(settings.MEDIA_ROOT / Path(name).name, "rb") as file:
            data = file.read()
        file.close()        
        response = HttpResponse(data,content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename='+name
        return response

def getImage(name):
    aadhar_no = ""
    mysqlConnect = connect_to_database()
    with mysqlConnect:
        result = mysqlConnect.cursor()
        result.execute("select aadhar_img, aadhar_no from patients where patient_name='"+name+"'")
        lists = result.fetchall()
        for ls in lists:
            name = ls[0]
            aadhar_no = ls[1]
            break
    return name, aadhar_no

def AdminPatientView(request):
    if request.method == 'GET':
        global username
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Appointment ID</font></th>'
        output+='<th><font size=3 color=black>Patient Name</font></th>'
        output+='<th><font size=3 color=black>Doctor Name</font></th>'
        output+='<th><font size=3 color=black>Disease Details</font></th>'
        output+='<th><font size=3 color=black>Prescription</font></th>'
        output+='<th><font size=3 color=black>Appointment Date</font></th>'
        output+='<th><font size=3 color=black>Booking Date</font></th>'
        output+='<th><font size=3 color=black>Aadhar No</font></th>'
        output+='<th><font size=3 color=black>Aadhar Image</font></th>'
        output+='<th><font size=3 color=black>Download Medical History</font></th></tr>'
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select * from appointment")
            lists = result.fetchall()
            for ls in lists:
                img,aadhar_no = getImage(ls[1])
                output+='<tr><td><font size=3 color=black>'+str(ls[0])+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[2]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[3]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[4]+'</font></td>'
                output+='<td><font size=3 color=black>'+str(ls[5])+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[6]+'</font></td>'
                output+='<td><font size=3 color=black>'+aadhar_no+'</font></td>'
                output+='<td><img src="/media/'+Path(img).name+'" width="400" height="400"></img></td>'
                output +='<td><a href=\'DownloadAction?requester='+ls[1]+'\'><font size=3 color=white>Download</font></a></td></tr>'                  
        context= {'data':output}            
        return render(request,'AdminScreen.html', context)

def ViewAppointments(request):
    if request.method == 'GET':
        global username
        today = datetime.now()
        month = str(today.month)
        year = str(today.year)
        day = str(today.day)
        date = str(year) + "-" + str(month) + "-" + str(day)
        appointments = []
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select * from appointment where doctor_name='" + username + "' and appointment_date='" + date + "'")
            lists = result.fetchall()
            for ls in lists:
                img, aadhar_no = getImage(ls[1])
                masked_aadhar = ''.join([aadhar_no[k] if k < 8 else 'X' for k in range(len(aadhar_no))])
                appointments.append({
                    'appointment_id': ls[0],
                    'patient_name': ls[1],
                    'doctor_name': ls[2],
                    'disease_details': ls[3],
                    'prescription': ls[4],
                    'appointment_date': ls[5],
                    'booking_date': ls[6],
                    'aadhar_no': masked_aadhar,
                    'patient_image': img,
                    'download_url': 'DownloadAction?requester=' + ls[1],
                    'prescription_url': 'GeneratePrescription?pid=' + str(ls[0]) if ls[4] == 'Pending' else None,
                })
        context = {
            'appointments': appointments,
            'date': date,
            'username': username,
        }
        return render(request, 'DoctorAppointments.html', context)

def BookAppointment(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Doctor Name</font></th>'
        output+='<th><font size=3 color=black>Phone No</font></th>'
        output+='<th><font size=3 color=black>Email ID</font></th>'
        output+='<th><font size=3 color=black>Address</font></th>'
        output+='<th><font size=3 color=black>Description</font></th>'
        output+='<th><font size=3 color=black>Book Appointment</font></th></tr>'
        mysqlConnect = connect_to_database()
        with mysqlConnect:
            result = mysqlConnect.cursor()
            result.execute("select username,phone_no,email,address,description from user_signup where usertype='Doctor'")
            lists = result.fetchall()
            for ls in lists:
                output+='<tr><td><font size=3 color=black>'+ls[0]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[2]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[3]+'</font></td>'
                output+='<td><font size=3 color=black>'+ls[4]+'</font></td>'
                output+='<td><a href=\'Appointment?doctor='+ls[0]+'\'><font size=3 color=black>Click Here to Book Appointment</font></a></td></tr>'
        context= {'data':output}        
        return render(request,'PatientScreen.html', context)    

def index(request):
    if request.method == 'GET':
        return render(request,'index.html', {})

def AdminLogin(request):
    if request.method == 'GET':
        return render(request,'AdminLogin.html', {})    

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})
    
def DoctorLogin(request):
    if request.method == 'GET':
       return render(request, 'DoctorLogin.html', {})

def PatientLogin(request):
    if request.method == 'GET':
       return render(request, 'PatientLogin.html', {})

def InsuranceLogin(request):
    if request.method == 'GET':
       return render(request, 'InsuranceLogin.html', {})    

def isUserExists(username):
    is_user_exists = False
    global details
    mysqlConnect = connect_to_database()
    with mysqlConnect:
        result = mysqlConnect.cursor()
        result.execute("select * from user_signup where username='"+username+"'")
        lists = result.fetchall()
        for ls in lists:
            is_user_exists = True
    return is_user_exists    

def RegisterAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
        desc = request.POST.get('t6', False)
        usertype = request.POST.get('t7', False)
        record = isUserExists(username)
        page = None
        if record == False:
            dbconnection = connect_to_database()
            dbcursor = dbconnection.cursor()
            qry = "INSERT INTO user_signup(username,password,phone_no,email,address,description,usertype) VALUES('"+str(username)+"','"+password+"','"+contact+"','"+email+"','"+address+"','"+desc+"','"+usertype+"')"
            dbcursor.execute(qry)
            dbconnection.commit()
            if dbcursor.rowcount == 1:
                data = "Signup Done! You can login now"
                context= {'data':data}
                return render(request,'Register.html', context)
            else:
                data = "Error in signup process"
                context= {'data':data}
                return render(request,'Register.html', context) 
        else:
            data = "Given "+username+" already exists"
            context= {'data':data}
            return render(request,'Register.html', context)


def checkUser(uname, password, utype):
    global username
    msg = "Invalid Login Details"
    mysqlConnect = connect_to_database()
    with mysqlConnect:
        result = mysqlConnect.cursor()
        result.execute("select * from user_signup where username='"+uname+"' and password='"+password+"' and usertype='"+utype+"'")
        lists = result.fetchall()
        for ls in lists:
            msg = "success"
            username = uname
            break
    return msg

def PatientLoginAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        msg = checkUser(username, password, "Patient")
        if msg == "success":
            context = {'data': "Welcome " + username}
            return render(request, 'PatientScreen.html', context)
        else:
            context = {'data': msg}
            return render(request, 'PatientLogin.html', context)
        
def DoctorLoginAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        msg = checkUser(username, password, "Doctor")
        if msg == "success":
            context = {'data': "Welcome " + username}
            return render(request, 'DoctorScreen.html', context)
        else:
            context = {'data': msg}
            return render(request, 'DoctorLogin.html', context)

def DoctorScreen(request):
    global username
    context = {'data': "Welcome " + username}
    return render(request, 'DoctorScreen.html', context)
        
def AdminLoginAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        if username == os.environ.get("ADMIN_USERNAME") and password == os.environ.get("ADMIN_PASSWORD"):
            context = {'data': "Welcome " + username}
            return render(request, 'AdminScreen.html', context)
        else:
            context = {'data': msg}
            return render(request, 'AdminLogin.html', context)


def InsuranceLoginAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        msg = checkUser(username, password, "Insurance")
        if msg == "success":
            context= {'data':"Welcome "+username}
            return render(request,'InsuranceScreen.html', context)
        else:
            context= {'data':msg}
            return render(request,'InsuranceLogin.html', context)




        


        
