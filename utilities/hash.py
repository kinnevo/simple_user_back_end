# Method 1: Using bcrypt (RECOMMENDED for passwords)
import bcrypt

password = "012345"
# Convert the password to bytes
password_bytes = password.encode('utf-8')
# Generate a salt and hash the password
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(password_bytes, salt)

print(hashed_password)  # This will print the hashed password

# To verify later:
# def verify_password(plain_password, hashed_password):
#     return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)