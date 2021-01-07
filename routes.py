from flask import render_template, url_for, redirect, flash, request, abort
from __init__ import app, db, bcrypt, mail
from myform import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm
from model import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message



@app.route("/")
def home():
    return render_template('home.html')


@app.route("/register",methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

  

@app.route("/login",methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()   
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user,remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessfull! Please check email and password.', 'danger')
        
    return render_template('login.html',form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account",methods=['POST','GET'])
@login_required
def account():
    image_file= url_for('static', filename='profilepics/' + current_user.image_file) 
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your Profile is Updated!','success')
    elif request.method=='GET':
        form.username.data = current_user.username
        form.email.data = current_user.email    
    return render_template('account.html',form=form, image_file=image_file)


@app.route("/posts",methods=['GET'])
@login_required
def blogpost():
    if request.method=='GET':
        page = request.args.get('page', 1, type=int)
        all_post=Post.query.paginate(page=page, per_page=3)
        return render_template('posts.html',posts=all_post)


@app.route("/posts/newpost", methods=['POST', 'GET'])
@login_required
def newpost():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your Post has been created!', 'success')
        return redirect(url_for('blogpost'))
    return render_template('newpost.html', form=form)

@app.route("/posts/<int:id>/delete")
def delete(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        flash('You are not author of this post. You can not delete or update this post.','danger')
    else:    
        db.session.delete(post)
        db.session.commit()
        flash('Your post has been deleted!', 'success')
    return redirect('/posts')    


@app.route("/posts/<int:id>/edit", methods=['POST','GET'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!','success')
        return redirect(url_for('blogpost', id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('edit.html', form=form )
    

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='xyz@gmail.com', recipients=[user.email])
    msg.body = f'''To Reset Your Password, visit the following link:
{url_for('reset_token', token=token, _external=True)}    
    
'''
    mail.send(msg)

 
@app.route('/reset_password', methods=['POST', 'GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent to reset password','info')
        return redirect(url_for(login))
    return render_template('reset_request.html', form=form)


@app.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been reseted! You are now able to login', 'success')
        return redirect(url_for('login'))   
    return render_template('reset_token.html', form=form)
    



    
if __name__ == "__main__":
    app.run(debug=True)