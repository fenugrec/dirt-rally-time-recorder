Del /F dirtrally-lb.db
bin\sqlite3 -batch -init resources\setup-dr2.sql dirtrally-lb.db .exit 
pyinstaller timerecord.spec --noconfirm