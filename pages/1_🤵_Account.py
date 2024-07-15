import streamlit as st
import pymongo
from otp_test import generateOTP, send_otp

# Diagnostic check to print available secrets keys and MongoDB connection string
st.write("Available secrets keys:", st.secrets.keys())

try:
    # Load MongoDB connection string from secrets
    mongodb_connect = st.secrets["mongodb_atlas"]["mongodb_connect"]
    st.write("MongoDB connection string loaded successfully.")
    st.write("MongoDB connection string:", mongodb_connect)
except KeyError as e:
    st.error(f"KeyError: {e}")
except Exception as e:
    st.error(f"Error loading MongoDB connection string: {e}")

def update_password(email, new_password):
    myclient = pymongo.MongoClient(mongodb_connect)
    mydb = myclient["Brainwave"]
    mycol = mydb["Login_Credentials"]

    result = mycol.update_one(
        {"Mail": email},
        {"$set": {"Password": new_password}}
    )

def email_exists(email):
    myclient = pymongo.MongoClient(mongodb_connect)
    mydb = myclient["Brainwave"]
    mycol = mydb["Login_Credentials"]
    
    if mycol.find_one({"Mail": email}):
        return True
    else:
        return False

@st.experimental_dialog("🔑 Reset Your Password")
def verify_popup(mail, otp_generated):
    st.write(f"Verification OTP sent on your mail '{mail}'")
    
    otp = st.text_input("Enter Your OTP: ")
    if otp:
        if otp == otp_generated:
            st.success("✔️ OTP verified successfully")
            pass1 = st.text_input("Enter New Password:", type='password')
            pass2 = st.text_input("Enter Password once again:", type='password')
        else:
            st.error("❌ Please enter correct OTP")

    if st.button("Submit"):
        if pass1 != pass2:
            st.warning("Please enter the same passwords !!")
        elif len(pass1) < 8:
            st.warning("Password length should be at least 8 characters !!")
        else:
            update_password(mail, pass1)
            st.success("👍 Your password is updated")

def sign_up(name, mail, pwd):
    if not name or not mail or not pwd:
        return False, "⚠️ All fields are required."

    myclient = pymongo.MongoClient(mongodb_connect)
    mydb = myclient["Brainwave"]
    mycol = mydb["Login_Credentials"]

    if mycol.find_one({"Mail": mail}):
        return False, "Email already exists."
    
    info = {"Name": name, "Mail": mail, "Password": pwd}
    mycol.insert_one(info)
    return True, "Account created successfully!"

def sign_in(mail, pwd):
    if not mail or not pwd:
        return None

    myclient = pymongo.MongoClient(mongodb_connect)
    mydb = myclient["Brainwave"]
    mycol = mydb["Login_Credentials"]

    user = mycol.find_one({"Mail": mail, "Password": pwd})
    if user:
        return user
    else:
        return None

def handle_login():
    userinfo = sign_in(st.session_state.email_input, st.session_state.password_input)
    if userinfo:
        st.session_state.username = userinfo['Name']
        st.session_state.useremail = userinfo['Mail']
        st.session_state.signedout = True
        st.session_state.signout = True
    else:
        st.warning('⚠️ Login Failed')

def handle_logout():
    st.session_state.signout = False
    st.session_state.signedout = False
    st.session_state.username = ''
    st.session_state.useremail = ''
    del st.session_state.username

st.title('Welcome to :violet[BrainWave] :sunglasses:')

if 'useremail' not in st.session_state:
    st.session_state.useremail = ''
if "signedout" not in st.session_state:
    st.session_state["signedout"] = False
if 'signout' not in st.session_state:
    st.session_state['signout'] = False

if not st.session_state["signedout"]:
    choice = st.selectbox('Login/Signup', ['Sign up', 'Login', 'forgot password'])

    if choice == "Sign up":
        username = st.text_input('👤 Enter unique username')
        email = st.text_input('📧 Email Address')
        password = st.text_input('🔑 Password', type='password')

        if st.button("Register"):
            success, message = sign_up(username, email, password)
            if success:
                st.success(message)
                st.balloons()
            else:
                st.warning(message)

    elif choice == "Login":
        email = st.text_input('📧 Email Address')
        password = st.text_input('🔑 Password', type='password')

        st.session_state.email_input = email
        st.session_state.password_input = password

        st.button('Login', on_click=handle_login)

    else:
        otp_generated = generateOTP()

        sender_email = "anannya0316@gmail.com"
        password = st.secrets['mail_pwd']  # Your App Password
        subject = "BrainWave password recovery"
        body = f"Verification OTP for password recovery - {otp_generated}."

        if "vote" not in st.session_state:
            reset_mail = st.text_input("Enter your registered mail:")

        if st.button("NEXT"):
            if reset_mail and not email_exists(reset_mail):
                st.error("❌ Your mail is not registered with BrainWave")
            else:
                send_otp(sender_email, reset_mail, password, subject, body)
                verify_popup(reset_mail, otp_generated)

if st.session_state.signout:
    st.success(f"✔️ logged in as :- **{st.session_state.username}**")

    st.markdown("### ✨ Explore the features of our project ")
    st.write("1) 📂 **Project Management** : Organize your notes and documents project-wise.")
    st.write("2) 💬 **Chat with Documents** : Interact with your PDFs and CSVs through an intuitive chat interface.")
    st.write("3) 📝 **Document Summarization** : Generate concise summaries of your PDF documents.")

    st.button('Sign out', on_click=handle_logout)
