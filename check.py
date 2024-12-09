from passlib.hash import pbkdf2_sha256

# The hashed password stored in the database
hashed_password = "$pbkdf2-sha256$29000$IoQwBkCoNWbsXWsNwfg/pw$IF5/XReTdNDjD9uy2XyjKMIRd7CgVSvuR/PQaKxq5E4"
# The password provided by the user
password = "kamran123"

# Verify the password
is_correct = pbkdf2_sha256.verify(password, hashed_password)

# Print the result
print("Password is correct:", is_correct)
