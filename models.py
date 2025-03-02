from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Satellite(Base):
    __tablename__ = 'satellites'
    __table_args__ = {'schema': 'satelite'}

    norad_id = Column(String, primary_key=True)
    name = Column(String)
    tle_line1 = Column(String)
    tle_line2 = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

    users = relationship('User', secondary='satelite.user_satellite', back_populates='satellites')


class UserSatellite(Base):
    __tablename__ = 'user_satellite'
    __table_args__ = {'schema': 'satelite'}

    user_id = Column(Integer, ForeignKey('satelite.users.id'), primary_key=True)
    norad_id = Column(String, ForeignKey('satelite.satellites.norad_id'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'satelite'}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AuthToken(Base):
    __tablename__ = 'auth_tokens'
    __table_args__ = {'schema': 'satelite'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('satelite.users.id'))
    token = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    user = relationship('User', back_populates='tokens')

User.tokens = relationship('AuthToken', back_populates='user')
User.satellites = relationship('Satellite', secondary='satelite.user_satellite', back_populates='users')

