from flask import Flask, flash, render_template, request, session, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from sqlalchemy.sql.expression import func, select
import os
import json
from passlib.hash import pbkdf2_sha256
from datetime import datetime
import secrets
import sqlite3
from models import *


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
db = SQLAlchemy()
app.config['WTF_CSRF_SECRET_KEY'] = "b'f\xfa\x8b{X\x8b\x9eM\x83l\x19\xad\x84\x08\xaa"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost:3306/tms"
app.config['SECRET_KEY'] = "b'f\xfa\x8b{X\x8b\x9eM\x83l\x19\xad\x84\x08\xaa"
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static\\packimages\\')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Initialize
db.init_app(app)



def save_images(photo):
    hash_photo= secrets.token_urlsafe(20)
    _, file_extension = os.path.splitext(photo.filename)
    photo_name= hash_photo + file_extension
    file_path= os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], photo_name)
    photo.save(file_path)
    return photo_name

# Guest - Home Page
@app.route("/")
def home():
    packs = Tbltourpackages.query.order_by(Tbltourpackages.Creationdate.desc()).all()
    random = Tbltourpackages.query.order_by(func.random()).all()
    return render_template('index.html', packs=packs, random=random)


#   Guest - All Packages
@app.route("/trips-list")
def trips():
    packs = Tbltourpackages.query.order_by(Tbltourpackages.Creationdate.desc()).all()
    random = Tbltourpackages.query.order_by(func.random()).all()
    return render_template('package-list.html', packs=packs, random=random)

#  Guest - Contact Us
@app.route("/contact-us")
def contact():
    packs = Tbltourpackages.query.order_by(Tbltourpackages.Creationdate.desc()).all()
    random = Tbltourpackages.query.order_by(func.random()).all()
    return render_template('contact.html', packs=packs, random=random)

# Guest - View Trip Details
@app.route("/trip_id=<id>" , methods=['POST','GET'])
def booking(id):
    result = db.session.query(Tbltourpackages).filter(Tbltourpackages.PackageId==id).first()
    usr= db.session.query(User).filter(User.id==session.get('uid')).first()
    if result:
        if request.method == 'POST':
            if session.get('user'):
                city= request.form.get('city')
                date= request.form.get('date')
                msg= request.form.get('message')
                bk= Tblbooking(PackageId=id, UserId=session.get('uid'), city=city, FromDate=date, Comment=msg, status='3')
                db.session.add(bk)
                db.session.commit()
                flash('Your Trip is Submitted')
                return redirect(url_for('booking_history'))
            else:
                return redirect(url_for('signin'))
        else:
            return render_template('booking-page.html',  result=result, usr=usr)
    else:
        return render_template('404.html')


# User - USER SIGNUP
@app.route("/signup", methods=['POST','GET'])
def signup():
    if session.get('user'):
        return redirect(url_for('user'))
    else:
        if request.method == 'POST':
            fullname = request.form.get('fullname')
            email = request.form.get('email')
            mobile = request.form.get('mobile')
            passw = request.form.get('password')
            password = pbkdf2_sha256.hash(passw)
            cur= User.query.filter_by(email=email).first()
            if cur is None:
                usr= User(fullname=fullname,email=email, mobile=mobile ,password=password)
                db.session.add(usr)
                db.session.commit()
                return redirect(url_for('signin'))
            else:
                error = 'username already exist choose another!'
                return render_template("user/pages-register.html", error=error)
        else:
            return render_template("user/pages-register.html")

# Admin - ADMIN LOGIN
@app.route("/admin" , methods=['POST','GET'])
def login():
     if session.get('admin'):
         return redirect(url_for('admin'))
     elif session.get('user'):
         session.clear()
         return render_template("admin/pages-login.html")
     else:
         if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            adm = Admin.query.filter_by(username=username).first()
            if adm and pbkdf2_sha256.verify(password, adm.password):
                session['admin'] = adm.username
                session['aid']= adm.id
                return redirect(url_for('admin'))
            else:
                error='Invalid Username or Password'
                return render_template("admin/pages-login.html", error=error)
         else:
             return render_template("admin/pages-login.html")


# User - User Login Page
@app.route("/login" , methods=['POST','GET'])
def signin():
     if session.get('user'):
         return redirect(url_for('user'))
     elif session.get('admin'):
         session.clear()
         return render_template("user/pages-login.html")
     else:
         if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            usr = User.query.filter_by(email=email).first()
            if usr and pbkdf2_sha256.verify(password, usr.password):
                session['user'] = usr.email
                session['uid']= usr.id

                session['username']= usr.fullname
                return redirect(url_for('user'))
            else:
                error='Invalid Email or Password'
                return render_template("user/pages-login.html", error=error)
         else:
             return render_template("user/pages-login.html")

# User - USER DASHBOARD
@app.route("/user_dashboard")
def user():
    if session.get('user'):
        return render_template("user/user.html")
    else:
        flash('LOGIN FIRST TO ACCESS DASHBOARD')
        return redirect(url_for('signin'))


#  Admin - ADMIN DASHBOARD
@app.route("/dashboard")
def admin():
    if session.get('admin'):
        member= User.query.all()
        bkk = Tblbooking.query.all()
        cats = Tbltourpackages.query.all()
        mgs = Chat.query.all()
        booking = db.session.query(User, Tblbooking, Tbltourpackages).filter(Tblbooking.UserId == User.id).filter(
            Tblbooking.PackageId == Tbltourpackages.PackageId) \
            .order_by(Tblbooking.RegDate.desc()).all()
        msg= db.session.query(Chat,User).filter(Chat.uid==User.id).filter(Chat.sender>1).order_by(Chat.time.desc()).all()
        return render_template("admin/admin.html",cats=cats,bkk=bkk, mgs=mgs, member=member, booking=booking, msg=msg)
    else:
        flash('LOGIN FIRST TO ACCESS DASHBOARD')
        return redirect(url_for('login'))

# Admin - ADMIN ADD NEW TOUR
@app.route("/add-tour", methods=['POST','GET'])
def add_tour():
    if session.get('admin'):
        if request.method == 'POST':
            title = request.form.get('title')
            location = request.form.get('location')
            transport = request.form.get('transport')
            meal = request.form.get('meal')
            accommodation = request.form.get('accommodation')
            duration = request.form.get('duration')
            pdetails = request.form.get('editor')
            price = request.form.get('price')
            f = save_images(request.files.get('timage'))
            tour = Tbltourpackages(PackageName=title, PackageDetails=pdetails, PackageLocation=location, Transport=transport, Meal=meal,Duration=duration,
                                   Accommodation=accommodation,PackagePrice=price, PackageImage =f)
            db.session.add(tour)
            db.session.commit()
            flash("TOUR ADDED SUCCESSFULLY")
            return redirect(url_for('manage_tours'))
        else:
            return render_template("admin/add-tour.html")
    else:
        flash('LOGIN FIRST TO PROCEED')
        return render_template("admin/pages-login.html")


#  Admin - EDIT TOUR INFORMATION
@app.route("/manage-tour/id=<id>/action=edit", methods=['POST', 'GET'])
def edit_tour(id):
    if session.get('admin'):
        if request.method == 'POST':
            img= request.files.get('timage')
            title = request.form.get('title')
            location = request.form.get('location')
            transport = request.form.get('transport')
            meal = request.form.get('meal')
            accommodation = request.form.get('accommodation')
            duration = request.form.get('duration')
            tdetails = request.form.get('editor')
            price = request.form.get('price')
            hello= Tbltourpackages.query.filter_by(PackageId=id).first()
            _, file_extension = os.path.splitext(img.filename)
            if ('.jpg' or '.jpeg' or '.png') in file_extension:
                updte = db.session.query(Tbltourpackages).filter_by(PackageId=id).first()
                os.remove(app.config['UPLOAD_FOLDER']+updte.PackageImage)
                updte.PackageName = title
                updte.PackageLocation = location
                updte.PackageImage = save_images(request.files.get('timage'))
                updte.Transport = transport
                updte.Meal = meal
                updte.Accommodation = accommodation
                updte.Duration = duration
                updte.PackagePrice = price
                updte.PackageDetails = tdetails
                db.session.commit()
                flash("CHANGES WERE MADE SUCCESSFULLY")
                return redirect(url_for('manage_tours'))
            else:
                updte = db.session.query(Tbltourpackages).filter_by(PackageId=id).first()
                updte.PackageName = title
                updte.PackageLocation = location
                updte.PackageImage = hello.PackageImage
                updte.Transport = transport
                updte.Meal = meal
                updte.Accommodation = accommodation
                updte.Duration = duration
                updte.PackagePrice = price
                updte.PackageDetails = tdetails
                db.session.commit()
                flash("POST AS BEEN UPDATED")
                return redirect(url_for('manage_tours'))
        else:
            t = db.session.query(Tbltourpackages).filter(Tbltourpackages.PackageId==id).first()
            if t:
                return render_template("admin/edit-tour.html", id=id,t=t)
            else:
                return render_template('404.html')
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))


#  Admin - DELETE A TOUR PACKAGE
@app.route("/edit-tour/action_delete=<int:id>", methods=['POST','GET'])
def delete_pack(id):
    if session.get('admin'):
        post = db.session.query(Tbltourpackages).filter_by(PackageId=id).first()
        if post is None:
            flash("This Item is Already Deleted")
            return redirect(url_for('manage_tours'))
        else:
            record= db.session.query(Tbltourpackages).filter_by(PackageId=id).first()
            os.remove(app.config['UPLOAD_FOLDER']+record.PackageImage)
            db.session.delete(record)
            db.session.commit()
            flash('Package Has been Deleted')
            return redirect(url_for('manage_tours'))
    else:
        flash('LOGIN FIRST TO PROCEED')
        return render_template("admin/pages-login.html")


#  Admin - MANAGE BOOKINGS
@app.route("/manage-bookings",  methods=['POST','GET'])
def manage_bookings():
    if session.get('admin'):
        if request.method == 'POST':
            st = request.form.get('myselect')
            bkid= request.form.get('bkid')
            bk = db.session.query(Tblbooking).filter_by(BookingId=bkid).first()
            bk.status = st
            db.session.commit()
            return redirect(request.url)
        else:
            booking = db.session.query(User, Tblbooking, Tbltourpackages).filter(Tblbooking.UserId==User.id).filter(Tblbooking.PackageId==Tbltourpackages.PackageId)\
            .order_by(Tblbooking.RegDate.desc()).all()
            return render_template("admin/bookings.html",booking=booking)
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))


#   Admin - MANAGE TOURS
@app.route("/manage-tours")
def manage_tours():
    if session.get('admin'):
        tours = db.session.query(Tbltourpackages).order_by(Tbltourpackages.Creationdate.desc()).all()

        return render_template("admin/manage-packages.html",tours=tours)
    else:
        flash('LOGIN FIRST TO PROCEED')
        return render_template("admin/pages-login.html")

#  Admin -  GUEST USER CONTACT HELP
@app.route("/manage-help",  methods=['POST','GET'])
def guest_help():
    if session.get('admin'):
        if request.method == 'POST':
            id= request.form.get('eqid')
            st= request.form.get('st')
            stats = db.session.query(TblEnquiry).filter_by(id=id).first()
            stats.Status = st
            db.session.commit()
            return redirect(request.url)
        else:
            msg = TblEnquiry.query.order_by(TblEnquiry.PostingDate.desc()).all()
            return render_template("admin/guest-help.html",msg=msg)
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))

#   Admin -  MANAGE USERS
@app.route("/manage-users")
def manage_users():
    if session.get('admin'):
        users = User.query.order_by(User.regdate.desc()).all()

        return render_template("admin/manage-users.html",users=users)
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))

#  User -  USER BOOKING HISTORY
@app.route("/booking-history")
def booking_history():
    if session.get('user'):
        b = db.session.query(Tblbooking,Tbltourpackages).filter(Tblbooking.UserId==session.get('uid')).filter(Tblbooking.PackageId==Tbltourpackages.PackageId)\
            .order_by(Tblbooking.RegDate.desc()).all()

        return render_template("user/booking-history.html",b=b)
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('user'))

# User -  User Chat Screen
@app.route("/chat" , methods=['POST','GET'])
def uchat():
    if session.get('user'):
        if request.method == 'POST':
            msg = request.form.get('msg')
            cht = Chat(uid=session.get('uid'), message=msg, sender=session.get('uid'), status='2')
            db.session.add(cht)
            db.session.commit()
            return redirect(request.url)
        else:
            result = db.session.query(Chat,User).filter(Chat.uid==session.get('uid')).filter(User.id==session.get('uid')).order_by(Chat.time).all()
            user= About.query.filter(About.id==1).first()
            return render_template("user/apps-chat.html",user=user, result=result)

    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('signin'))

# Admin -  ADMIN CHAT SCREEN
@app.route("/chat=<uid>" , methods=['POST','GET'])
def chat(uid):
    if session.get('admin'):
        if request.method == 'POST':
            msg = request.form.get('msg')
            cht = Chat(uid=uid, message=msg, sender=session.get('aid'), status='1')
            db.session.add(cht)
            db.session.commit()
            return redirect(request.url)
        else:
            result = Chat.query.filter(Chat.uid==uid).order_by(Chat.time).all()
            user= User.query.filter(User.id==uid).first()
            if user:
                return render_template("admin/apps-chat.html",user=user, result=result, uid=uid)
            else:
                return render_template('404.html')

    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))

# Admin -  ADMIN CONTACT HELP NOTIFICATIONS
@app.route("/help", methods=['POST','GET'])
def help():
    if session.get('admin'):
        if request.method == 'POST':
            status = request.form.get('read')
            uid = request.form.get('usr')
            cht = request.form.get('cht')
            ch= db.session.query(Chat).filter_by(id=cht).first()
            ch.status=status
            db.session.commit()
            return redirect("../chat="+uid)
        else:
            u = User.query.all()
            r = db.session.query(Chat, User).filter(User.id==Chat.uid).order_by(Chat.time.desc()).all()
            return render_template("admin/chat.html", u=u, r=r)
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))


#  Admin -  EDIT PAGE TYPES
@app.route("/page_type=<type>", methods=['POST','GET'])
def pges(type):
    if session.get('admin'):
        if request.method == 'POST':
            detail = request.form.get('editor')
            typ= db.session.query(Tblpages).filter_by(type=type).first()
            typ.detail=detail
            db.session.commit()
            return redirect('page_type='+type)
        else:
            t = db.session.query(Tblpages).filter_by(type=type).first()
            if t:
                return render_template("admin/pages.html", t=t)
            else:
                return render_template('404.html')
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))


#  EDIT CONTACT INFO
@app.route("/edit-contact", methods=['POST','GET'])
def edit_contact():
    if session.get('admin'):
        if request.method == 'POST':
            aid = request.form.get('aid')
            phone = request.form.get('phone')
            email = request.form.get('email')
            abt= db.session.query(About).filter_by(id=aid).first()
            abt.email=email
            abt.phone=phone
            db.session.commit()
            return redirect(request.url)
        else:
            a= db.session.query(About).filter_by(id=1).first()
            return render_template("admin/edit-contact.html", a=a)
    else:
        flash('LOGIN FIRST TO PROCEED')
        return redirect(url_for('login'))


#  Guest contact(enquiry) Page
@app.route("/contact-us", methods=['POST','GET'])
def contact_us():
    if request.method == 'POST':
        fullname = request.form.get('fname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        subject = request.form.get('subject')
        description = request.form.get('msg')
        enq= TblEnquiry(FullName=fullname, EmailId=email, MobileNumber=phone, Subject=subject, Description=description, Status='2')
        db.session.add(enq)
        db.session.commit()
        flash('MESSAGE HAS BEEN SENT')
        return redirect(request.url)
    else:
        ct= db.session.query(Tbltourpackages).filter_by(id=1).first()
        print(ct.email)
        return render_template("contact.html", ct=ct)


#  GUEST USER PAGE TYPE
@app.route("/page_<type>")
def info(type):
            t = db.session.query(Tblpages).filter_by(type=type).first()
            if t:
                return render_template("page.html", t=t)
            else:
                return render_template('404.html')


#   UPDATE PROFILE SECTION
@app.route("/update-profile", methods=['POST','GET'])
def update_profile():
    if session.get('user'):
        if request.method=='POST':
            email= request.form.get('email')
            fname= request.form.get('fname')
            mobile= request.form.get('mobile')
            upt = db.session.query(User).filter_by(id=session.get('uid')).first()
            upt.email= email
            upt.fullname= fname
            upt.mobile = mobile
            db.session.commit()
            session['username'] = fname
            flash('PROFILE UPDATED SUCCESSFULLY')
            user = User.query.filter_by(id=session.get('uid')).first()
            return render_template('user/update-profile.html', user=user)
        else:
            user = User.query.filter_by(id=session.get('uid')).first()
            return render_template('user/update-profile.html', user=user)
    else:
        return redirect(url_for('signin'))



#   PASSWORD CHANGE SECTION
@app.route("/change-password", methods=['POST','GET'])
def change_password():
    if session.get('admin'):
        if request.method=='POST':
            oldpass=request.form.get('oldpass')
            password = pbkdf2_sha256.hash(request.form.get('password'))
            adm = Admin.query.filter_by(id=session.get('aid')).first()
            if pbkdf2_sha256.verify(oldpass, adm.password):
                upt = db.session.query(Admin).filter_by(id=session.get('aid')).first()
                upt.password = password
                db.session.commit()
                flash('PASSWORD UPDATED SUCCESSFULLY')
                return render_template("admin/change-password.html")
            else:
                error='YOUR OLD PASSWORD WAS INCORRECT'
                return render_template("admin/change-password.html", error=error)
        else:
            return render_template("admin/change-password.html")
    elif session.get('user'):
        if request.method=='POST':
            oldpass=request.form.get('oldpass')
            password = pbkdf2_sha256.hash(request.form.get('password'))
            usr = User.query.filter_by(id=session.get('uid')).first()
            if pbkdf2_sha256.verify(oldpass, usr.password):
                upt = db.session.query(User).filter_by(id=session.get('uid')).first()
                upt.password = password
                db.session.commit()
                flash('PASSWORD UPDATED SUCCESSFULLY')
                return render_template("user/change-password.html")
            else:
                error='YOUR OLD PASSWORD WAS INCORRECT'
                return render_template("user/change-password.html", error=error)
        else:
            return render_template("user/change-password.html")
    else:
        flash('LOGIN FIRST TO ACCESS DASHBOARD')
        return redirect(url_for('login'))

# Logout
@app.route("/logout")
def logout():
    if session.get('admin'):
        session.clear()
        return redirect(url_for('home'))
    elif session.get('user'):
        session.clear()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

# create  custom Error pages
#Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"),404

# Internal server error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"),500


if __name__ == "__main__":

    app.run(debug=True)
