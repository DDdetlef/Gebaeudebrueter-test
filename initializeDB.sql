create table gebaeudebrueter
(
    id              INTEGER
        primary key,
    web_id          INTEGER not null,
    bezirk          TEXT,
    plz             INTEGER not null,
    ort             text    not null,
    strasse         text    not null,
    anhang          text,
    erstbeobachtung TEXT,
    beschreibung    TEXT,
    besonderes      TEXT,
    checksum        TEXT,
    update_date     TEXT,
    new             INTEGER default 1,
    mauersegler     INTEGER default 0,
    kontrolle       INTEGER default 0,
    sperling        INTEGER default 0,
    ersatz          INTEGER default 0,
    schwalbe        INTEGER default 0,
    wichtig         INTEGER default 0,
    star            INTEGER default 0,
    sanierung       INTEGER default 0,
    fledermaus      INTEGER default 0,
    verloren        INTEGER default 0,
    andere          INTEGER default 0
);

create table geolocation_google
(
    id                 INTEGER
        primary key,
    web_id             INTEGER not null unique,
    longitude          REAL    not null,
    latitude           REAL    not null,
    location           TEXT    not null,
    complete_response  TEXT    not null
);

create table geolocation_osm
(
    id                 INTEGER primary key,
    web_id INTEGER not null unique,
    longitude          REAL    not null,
    latitude           REAL    not null,
    location           TEXT    not null,
    complete_response  TEXT    not null
);