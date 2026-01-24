import sqlite3
import matplotlib.pyplot as plt
from operator import add

try:
    sqliteConnection = sqlite3.connect('brueter.sqlite')
    cursor = sqliteConnection.cursor()
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)

cursor.execute('select strftime('\''%Y\'',erstbeobachtung) as year,count(*) from gebaeudebrueter group by cast(strftime('\''%Y\'',erstbeobachtung) as decimal)')
data = cursor.fetchall()

dates = []
amounts = []
for (date, amount) in data:
    if date is None:
        continue
    #print(type(date))
    dates.append(int(date))
    amounts.append(int(amount))

plt.plot(dates, amounts,'.-')
plt.xlabel('Jahr')
plt.ylabel('Erstbeobachtungen')
plt.savefig('erstbeobachtungProJahr.png',dpi=150)
plt.close()

cumulative = []
last = 0
for amount in amounts:
    new = amount + last
    cumulative.append(new)
    last = new

plt.plot(dates, cumulative, '.-')
plt.xlabel('Jahr')
plt.ylabel('kummulierte Erstbeobachtungen')
plt.savefig('erstbeobachtungKummuliertJahr.png',dpi=150)
plt.close()

cursor.execute('select strftime('\''%Y\'',erstbeobachtung) as year,count(*) from gebaeudebrueter where mauersegler = 1 group by cast(strftime('\''%Y\'',erstbeobachtung) as decimal)')
data_mauersegler = cursor.fetchall()
cursor.execute('select strftime('\''%Y\'',erstbeobachtung) as year,count(*) from gebaeudebrueter where sperling = 1 group by cast(strftime('\''%Y\'',erstbeobachtung) as decimal)')
data_sperling = cursor.fetchall()
cursor.execute('select strftime('\''%Y\'',erstbeobachtung) as year,count(*) from gebaeudebrueter where schwalbe = 1 group by cast(strftime('\''%Y\'',erstbeobachtung) as decimal)')
data_schwalbe = cursor.fetchall()
cursor.execute('select strftime('\''%Y\'',erstbeobachtung) as year,count(*) from gebaeudebrueter where star = 1 group by cast(strftime('\''%Y\'',erstbeobachtung) as decimal)')
data_star = cursor.fetchall()
cursor.execute('select strftime('\''%Y\'',erstbeobachtung) as year,count(*) from gebaeudebrueter where fledermaus = 1 group by cast(strftime('\''%Y\'',erstbeobachtung) as decimal)')
data_fledermaus = cursor.fetchall()
cursor.execute('select strftime('\''%Y\'',erstbeobachtung) as year,count(*) from gebaeudebrueter where andere = 1 group by cast(strftime('\''%Y\'',erstbeobachtung) as decimal)')
data_andere = cursor.fetchall()

label_default = list(range(min(dates),max(dates)+1))

value_mauersegler = [0] * len(label_default)
value_sperling = [0] * len(label_default)
value_schwalbe = [0] * len(label_default)
value_star = [0] * len(label_default)
value_fledermaus = [0] * len(label_default)
value_andere = [0] * len(label_default)

for (date, value) in data_mauersegler:
    if date is None:
        continue
    idx = label_default.index(int(date))
    value_mauersegler[idx]= int(value)

for (date, value) in data_sperling:
    if date is None:
        continue
    idx = label_default.index(int(date))
    value_sperling[idx] = int(value)

for (date, value) in data_schwalbe:
    if date is None:
        continue
    idx = label_default.index(int(date))
    value_schwalbe[idx] = int(value)

for (date, value) in data_star:
    if date is None:
        continue
    idx = label_default.index(int(date))
    value_star[idx] = int(value)

for (date, value) in data_fledermaus:
    if date is None:
        continue
    idx = label_default.index(int(date))
    value_fledermaus[idx] = int(value)

for (date, value) in data_andere:
    if date is None:
        continue
    idx = label_default.index(int(date))
    value_andere[idx] = int(value)

fig, ax = plt.subplots()
bottom = [0] * len(label_default)
ax.bar(label_default,value_sperling, bottom=bottom, label='Sperling')
bottom = list(map(add, bottom, value_sperling))

ax.bar(label_default,value_mauersegler, bottom=bottom , label='Mauersegler')
bottom = list(map(add, bottom, value_mauersegler))

ax.bar(label_default, value_schwalbe, bottom=bottom, label='Schwalbe')
bottom = list(map(add, bottom, value_schwalbe))

ax.bar(label_default,value_star, bottom=bottom, label='Star')
bottom = list(map(add, bottom, value_star))

ax.bar(label_default,value_fledermaus, bottom=bottom, label='Fledermaus')
bottom = list(map(add, bottom, value_fledermaus))

ax.bar(label_default,value_andere, bottom=bottom, label='Andere')
bottom = list(map(add, bottom, value_andere))

ax.legend()
plt.ylabel('Anzahl')
plt.xlabel('Jahr')
plt.savefig('artProJahr.png',dpi=150)
# plt.show()
cursor.close()
#plt.show()
