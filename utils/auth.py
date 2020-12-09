"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
def yibanLogin(username, password):
    return False

def checkPermission(user, action):
    if user is None:
        return False
    if action not in user["permission"]:
        return False
    if not user["permission"][action]:
        return False
    return True