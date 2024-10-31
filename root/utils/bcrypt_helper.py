import bcrypt

def to_bits(*args):
  return tuple(s.encode('utf-8') for s in args)

def to_str(*args):
  return tuple(b.decode('utf-8') for b in args)

def hash_pwd(pwd: str) -> str:
  salt = bcrypt.gensalt()
  return to_str(bcrypt.hashpw(*to_bits(pwd), salt))[0]

def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
  return bcrypt.checkpw(*to_bits(plain_pwd, hashed_pwd))