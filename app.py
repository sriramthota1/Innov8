import json
from flask import Flask, request, url_for, redirect, render_template  # mediator between server and client
import requests as reqs  # The requests module allows you to send HTTP requests using Python.
from datetime import datetime
from pytz import timezone
import os.path
import numpy as np
from werkzeug.utils import secure_filename
import face_recognition as fr
import cv2
import numpy as np
import os, shutil
import base64

app = Flask(__name__)


# Here i have read the data from gogle drive
def get_encoded_faces():
    encoded = {}
    for dirpath, dname, fname in os.walk("static/images/"):
        for f in fname:
            if f.endswith(".jpeg") or f.endswith(".jpg"):
                face = fr.load_image_file("static/images/" + f)
                encoding = fr.face_encodings(face)[0]
                encoded[f.split(".")[0]] = encoding
    return (encoded)


# Here i am recognising the face of test data by providing certain data
def classify_face(im):
    faces = get_encoded_faces()
    faces_encoded = list(faces.values())
    known_faces_names = list(faces.keys())

    img = cv2.imread(im)
    face_locations = fr.face_locations(img)
    unknown_face_encodings = fr.face_encodings(img, face_locations)
    face_names = []
    for face_encoding in unknown_face_encodings:
        name = "Unknown"
        matches = fr.compare_faces(faces_encoded, face_encoding)
        face_distances = fr.face_distance(faces_encoded, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_faces_names[best_match_index]
        face_names.append(name)
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            cv2.rectangle(img, (left - 20, top - 20), (right + 20, bottom + 20), (255, 0, 0), 2)
            cv2.rectangle(img, (left - 20, bottom - 15), (right + 20, bottom + 20), (255, 0, 0), cv2.FILLED)
            cv2.putText(img, name, (left - 20, bottom + 15), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
    while (True):
        # cv2_imshow(img)
        return (face_names)


@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')


@app.route('/markattendance.html', methods=['GET'])
def mark():
    return render_template('markattendance.html')


@app.route('/statistics.html', methods=['GET'])
def stat():
    return render_template('statistics.html')


@app.route('/teacherlogin.html', methods=['GET'])
def tlogin():
    # R
    return render_template('teacherlogin.html')


@app.route('/teacherregister.html', methods=['GET'])
def treg():
    # R
    return render_template('teacherregister.html')


@app.route('/register.html', methods=['GET'])
def reg():
    # R
    return render_template('register.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return "no picture"
    elif request.method == "POST":
        features = [(x) for x in request.form.values()]
        print(features)
        for i in features:
            print(i)
    import os.path
    directory = './static/images/'
    f_rollnum = features[0]
    f_name = features[1]

    # checking whether already existing record - Already Registered based on ROllID
    # Getting data from DB(server) to Client to compare the registered student with the newly scanned student pi
    response = reqs.get(
        'https://ap-south-1.aws.data.mongodb-api.com/app/trackmyattendance_portal-kexzf/endpoint/StudentRegister_GET')

    # Use the json module to load CKAN's response into a dictionary.
    data = json.loads(response.text)
    flag = 0
    n = len(data)
    for i in range(0, n):
        print(data[i])
        if data[i]['rollnumber'] == f_rollnum:
            return render_template('register.html',
                                   reg='Already Registered..!\n Same Rollnumber Student is present already and name is {}'.format(
                                       data[i]['name']))

    # if not already registered - Continues saving the Registration
    filename = f_name + '-' + f_rollnum + '.jpg'  # sriram-2070
    filepath = os.path.join(directory, filename)
    # print(f_name)
    im_value = features[5]
    imgdata = base64.b64decode(im_value[23:])
    with open(filepath, 'wb') as f:
        f.write(imgdata)
    f.close()
    print("Done")
    # Recording Resgistrations data from Client(WebApp) to server (DB) - POST
    data_send = reqs.post(
        'https://ap-south-1.aws.data.mongodb-api.com/app/trackmyattendance_portal-kexzf/endpoint/StudentRegister_POST',
        data={'rollnumber': features[0], 'name': features[1], 'year': features[2], 'branch': features[3],
              'section': features[4],
              'faceid': features[5]})
    print(data_send)
    return render_template('register.html',
                           reg='Registered Success')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == "GET":
        return "no picture"
    elif request.method == "POST":
        features = [(x) for x in request.form.values()]
        print(features)
        for i in features:
            print(i)
            print(i[23:])

        imgstring = i[23:]
        imgdata = base64.b64decode(imgstring)

        directory = './studentimgs/'
        now = datetime.now(timezone("Asia/Kolkata"))
        f_name = now.strftime("%d%m%Y %H%M%S")

        filename = f_name + '.jpg'
        filepath = os.path.join(directory, filename)
        # print(f_name)

        with open(filepath, 'wb') as f:
            f.write(imgdata)
        f.close()
        print("Done")

        print(classify_face(filepath))
        output = classify_face(filepath)

        # data to store into DB as attendance recorded
        # Add rollnum in Attendance collection
        date = now.strftime("%d/%m/%Y")
        time = now.strftime("%H:%M:%S")

        face_identity = imgstring

        # Getting data from DB(server) to Client to compare the registered student with the newly scanned student pi
        response = reqs.get(
            'https://ap-south-1.aws.data.mongodb-api.com/app/trackmyattendance_portal-kexzf/endpoint/StudentRegister_GET')

        # Use the json module to load CKAN's response into a dictionary.
        data = json.loads(response.text)
        flag = 0
        n = len(data)
        absentees = []
        for i in range(0, n):
            print(data[i])
            unique_id = str(data[i]['name']) + '-' + str(data[i]['rollnumber'])
            print(unique_id, output[0])
            if unique_id == output[0]:
                rno = data[i]['rollnumber']
                flag = 1
            cnt = 0
            for j in range(0, len(output)):
                if unique_id != output[j]:
                    cnt = cnt + 1
            if cnt == len(output):
                absentees.append(unique_id)
        if flag == 0:
            return render_template('markattendance.html',
                                   pred='Unregistered Student..!!!')
        elif flag == 1:
            name = classify_face(filepath)
            count = 0
        for i in name:
            if i == 'Unknown':
                print("unregistered")
            else:
                count = count + 1
                rno = i.split("-")
                print(rno[1])
                print(i)
                print(date)
                print(time)
                print(face_identity)

                data_send_attendance = reqs.post(
                    'https://ap-south-1.aws.data.mongodb-api.com/app/trackmyattendance_portal-kexzf/endpoint/MarkAttendence_POST',
                    data={'rollnumber': rno[1], 'name': i, 'date': date, 'time': time, 'faceid': face_identity})
                print(data_send_attendance)

            # recording the attendance into MongoDB - database collection - POST (sending data from client(WebApp) to DB via API)
            # data_send_attendance = reqs.post(
            #     'https://ap-south-1.aws.data.mongodb-api.com/app/trackmyattendance_portal-kexzf/endpoint/MarkAttendence_POST',
            #     data={'rollnumber': rno[1], 'name': i, 'date': date, 'time': time, 'faceid': face_identity})
            # print(data_send_attendance)

        time1=[]
        time=time.split(":")
        for i in time:
            time1.append(int(i))
        if time1[0]>=1 and time1[1]<=30:
            hour=1


        pdata = []
        for i in output:
            temp = i.split("-")
            temp.append(hour)
            pdata.append(temp)
        print(pdata)

        adata=[]
        for i in absentees:
            temp=i.split("-")
            adata.append(temp)

        return render_template('record.html',data1=pdata,data2=adata,count=count,alength=len(absentees))


if __name__ == '__main__':
    app.run(debug=True)

