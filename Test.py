import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#engine = create_engine(os.getenv("DATABASE_URL"))
engine = create_engine('mssql+pymssql://youxing:8601015@hp/C50W')
db = scoped_session(sessionmaker(bind=engine))

def main():
    flights = db.execute("select * from flights").fetchall()
    for flight in flights:
        print(flight.origin)

if __name__ == "__main__":
    main()
