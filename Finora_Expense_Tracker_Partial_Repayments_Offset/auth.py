import hashlib, os, hmac
from database import conn, now
ITERATIONS=310_000
def _hash(password,salt):
    return hashlib.pbkdf2_hmac("sha256",password.encode(),salt,ITERATIONS).hex()
def register_user(name,username,email,password):
    salt=os.urandom(16)
    try:
        with conn() as c:
            c.execute("INSERT INTO users(name,username,email,password_hash,salt,created_at) VALUES(?,?,?,?,?,?)",(name,username,email,_hash(password,salt),salt.hex(),now()))
        return True,"Account created."
    except Exception as e:
        if "UNIQUE" in str(e): return False,"That username is already taken."
        return False,"Could not create account. Please try again."
def login_user(username,password):
    from database import rows
    found=rows("SELECT * FROM users WHERE username=?",(username.strip(),))
    if not found: return None
    u=found[0]
    if hmac.compare_digest(_hash(password,bytes.fromhex(u["salt"])),u["password_hash"]):
        return {"id":u["id"],"name":u["name"],"username":u["username"]}
    return None
