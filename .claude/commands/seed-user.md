 ---
 description: Create a single dummy user in the database 
 
 alloweed-tools: head, Bash(python:*) 
 ---
 
 Read database/db.py to understand the users table 
 
 schema and the get_db() helper. 
 
 Then write and run a Python script using bash that: 
 
 1. Generates a realistic random indian user 
 using your 
    own knowledge of common indian names across regions: 
    - Name: a realistic Indian first + last name 
    - Email: derived from the name with a random 2-3 digit 
        number suffix (e.g. rahul.sharma91@gmail.com) 
    - password : "password123" hashed with werkzeug's generate_password_hash - created_at: current datetime 
    
2. checks if the generated email already exists in the 
    users table. If it doesn, regenerate until unique. 
    
3. Inserts the user into the database using the same 
    get_db() pattern found in db.py 
    
4. prints confirmation: 
    -id 
    -name 
    -email