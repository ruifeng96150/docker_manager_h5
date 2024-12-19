from flask_login import UserMixin
import os
from datetime import datetime, timedelta



class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def get_user():
        print('Getting user',os.getenv('APP_USERNAME'))
        return User(1, os.getenv('APP_USERNAME'))

    @staticmethod
    def check_credentials(username, password):
        return (username == os.getenv('APP_USERNAME') and
                password == os.getenv('APP_PASSWORD'))

class LoginAttemptTracker:
    def __init__(self):
        self.attempts = {}  # 记录登录尝试次数
        self.lockout_until = {}  # 记录锁定时间

    def can_attempt_login(self, username):
        now = datetime.now()

        # 检查是否在锁定期
        if username in self.lockout_until:
            print(f"User {username} is locked out until {self.lockout_until[username]}")
            if now < self.lockout_until[username]:
                # 计算剩余锁定时间
                remaining = self.lockout_until[username] - now
                remaining_minutes = int(remaining.total_seconds() / 60)
                return False, f"账号已被锁定，请等待 {remaining_minutes} 分钟后重试"
            else:
                # 锁定期已过，重置记录
                self.reset(username)

        return True, None

    def record_attempt(self, username, success):
        if success:
            # 登录成功，重置记录
            self.reset(username)
        else:
            # 登录失败，增加计数
            self.attempts[username] = self.attempts.get(username, 0) + 1

            # 检查是否需要锁定
            if self.attempts[username] >= 3:
                self.lockout_until[username] = datetime.now() + timedelta(minutes=60)
                self.attempts[username] = 0
                return False, "登录失败次数过多，账号已被锁定60分钟"
            else:
                remaining_attempts = 3 - self.attempts[username]
                return False, f"用户名或密码错误，还剩 {remaining_attempts} 次尝试机会"

        return True, None

    def reset(self, username):
        """重置用户的登录尝试记录"""
        if username in self.attempts:
            del self.attempts[username]
        if username in self.lockout_until:
            del self.lockout_until[username]

# 创建全局登录尝试追踪器实例
login_tracker = LoginAttemptTracker()
