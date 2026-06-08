import sqlite3
conn=sqlite3.connect('db.sqlite3')
c=conn.cursor()
ids=[8,603,1312,2001,352,661,1108]
for id in ids:
    c.execute('SELECT id,name,u_value,category FROM dashboard_ekobaudatmaterial WHERE id=?',(id,))
    row=c.fetchone()
    print(id,'->',row)
conn.close()
