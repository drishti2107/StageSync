
DROP TABLE IF EXISTS
    equipment, costume, prop, rehearsal_resource_checkout, resource,
    sound, music, light, sm_coord_scene_cue, cue,
    attendance, call_sheet, rehearsal_req_crew, rehearsal_req_cast,
    perf_reh_venue_book, rehearsal, venue, performance, stage_manager,
    char_appears_in_scene, scene, script, play_character,
    expense, budget, vendor,
    notif_crew, notif_cast, cast_availability, cast_member, crew_member,
    production, producer, director, schedule, notification
CASCADE;

CREATE TABLE notification (
    notification_id INTEGER      PRIMARY KEY,
    message         VARCHAR(200) NOT NULL,
    status          VARCHAR(10)  NOT NULL
                    CHECK (status IN ('Pending','Sent','Read','Failed')),
    sent_time       TIMESTAMP    NOT NULL
);

CREATE TABLE schedule      (schedule_id INTEGER PRIMARY KEY);
CREATE TABLE director      (director_id INTEGER PRIMARY KEY);
CREATE TABLE producer      (producer_id INTEGER PRIMARY KEY);
CREATE TABLE vendor        (vendor_id   INTEGER PRIMARY KEY);
CREATE TABLE stage_manager (sm_id       INTEGER PRIMARY KEY);

CREATE TABLE script (
    script_id INTEGER     PRIMARY KEY,
    version   VARCHAR(10) NOT NULL
);

CREATE TABLE venue (
    venue_id            INTEGER      PRIMARY KEY,
    address             VARCHAR(200) NOT NULL UNIQUE,
    capacity            INTEGER      NOT NULL CHECK (capacity > 0),
    availability_status VARCHAR(15)  NOT NULL
                        CHECK (availability_status IN ('Available','Booked','Maintenance'))
);

CREATE TABLE cue (
    cue_id   INTEGER PRIMARY KEY,
    sequence INTEGER NOT NULL CHECK (sequence > 0)
);

CREATE TABLE production (
    production_id INTEGER      PRIMARY KEY,
    title         VARCHAR(100) NOT NULL,
    type          VARCHAR(20)  NOT NULL
                  CHECK (type IN ('Play','Musical','Opera','Dance','Concert')),
    start_date    DATE         NOT NULL,
    end_date      DATE         NOT NULL,
    director_id   INTEGER      NOT NULL REFERENCES director(director_id)
                  ON UPDATE CASCADE ON DELETE RESTRICT,
    producer_id   INTEGER      NOT NULL REFERENCES producer(producer_id)
                  ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (end_date >= start_date)
);

CREATE TABLE crew_member (
    crew_id       INTEGER      PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    department    VARCHAR(20)  NOT NULL
                  CHECK (department IN ('Lighting','Sound','Costume','Props','Stage','Makeup','Set Design')),
    email         VARCHAR(100) NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%'),
    phone         VARCHAR(15)  NOT NULL CHECK (phone ~ '^[0-9+() -]{7,15}$'),
    schedule_id   INTEGER      NOT NULL REFERENCES schedule(schedule_id)
                  ON UPDATE CASCADE ON DELETE RESTRICT,
    production_id INTEGER      NOT NULL REFERENCES production(production_id)
                  ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE cast_member (
    cast_id       INTEGER      PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE CHECK (email LIKE '%_@_%._%'),
    phone         VARCHAR(15)  NOT NULL CHECK (phone ~ '^[0-9+() -]{7,15}$'),
    schedule_id   INTEGER      NOT NULL REFERENCES schedule(schedule_id)
                  ON UPDATE CASCADE ON DELETE RESTRICT,
    production_id INTEGER      NOT NULL REFERENCES production(production_id)
                  ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE cast_availability (
    cast_id        INTEGER NOT NULL REFERENCES cast_member(cast_id)
                   ON UPDATE CASCADE ON DELETE CASCADE,
    available_date DATE    NOT NULL,
    PRIMARY KEY (cast_id, available_date)
);

CREATE TABLE notif_cast (
    notification_id INTEGER NOT NULL REFERENCES notification(notification_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    cast_id         INTEGER NOT NULL REFERENCES cast_member(cast_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (notification_id, cast_id)
);

CREATE TABLE notif_crew (
    notification_id INTEGER NOT NULL REFERENCES notification(notification_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    crew_id         INTEGER NOT NULL REFERENCES crew_member(crew_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (notification_id, crew_id)
);

CREATE TABLE budget (
    budget_id           INTEGER       PRIMARY KEY,
    category            VARCHAR(50)   NOT NULL,
    contingency_amount  NUMERIC(12,2) NOT NULL CHECK (contingency_amount >= 0),
    producer_id         INTEGER       NOT NULL UNIQUE REFERENCES producer(producer_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE expense (
    expense_id INTEGER       PRIMARY KEY,
    amount     NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    approval   VARCHAR(10)   NOT NULL
               CHECK (approval IN ('Pending','Approved','Rejected')),
    budget_id  INTEGER       NOT NULL REFERENCES budget(budget_id)
               ON UPDATE CASCADE ON DELETE RESTRICT,
    vendor_id  INTEGER       NOT NULL REFERENCES vendor(vendor_id)
               ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE play_character (
    character_id INTEGER PRIMARY KEY,
    cast_id      INTEGER NOT NULL REFERENCES cast_member(cast_id)
                 ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE scene (
    scene_id  INTEGER PRIMARY KEY,
    script_id INTEGER NOT NULL REFERENCES script(script_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE char_appears_in_scene (
    character_id    INTEGER NOT NULL REFERENCES play_character(character_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    scene_id        INTEGER NOT NULL REFERENCES scene(scene_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    dialogue        TEXT    NOT NULL,
    stage_direction TEXT,
    PRIMARY KEY (character_id, scene_id)
);

CREATE TABLE performance (
    performance_id INTEGER PRIMARY KEY,
    sm_id          INTEGER NOT NULL REFERENCES stage_manager(sm_id)
                   ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE rehearsal (
    rehearsal_id INTEGER   PRIMARY KEY,
    start_time   TIMESTAMP NOT NULL,
    end_time     TIMESTAMP NOT NULL,
    producer_id  INTEGER   NOT NULL REFERENCES producer(producer_id)
                 ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (end_time > start_time)
);

CREATE TABLE perf_reh_venue_book (
    performance_id INTEGER NOT NULL REFERENCES performance(performance_id)
                   ON UPDATE CASCADE ON DELETE CASCADE,
    rehearsal_id   INTEGER NOT NULL REFERENCES rehearsal(rehearsal_id)
                   ON UPDATE CASCADE ON DELETE CASCADE,
    venue_id       INTEGER NOT NULL REFERENCES venue(venue_id)
                   ON UPDATE CASCADE ON DELETE RESTRICT,
    PRIMARY KEY (performance_id, rehearsal_id)
);

CREATE TABLE rehearsal_req_cast (
    rehearsal_id INTEGER NOT NULL REFERENCES rehearsal(rehearsal_id)
                 ON UPDATE CASCADE ON DELETE CASCADE,
    cast_id      INTEGER NOT NULL REFERENCES cast_member(cast_id)
                 ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (rehearsal_id, cast_id)
);

CREATE TABLE rehearsal_req_crew (
    rehearsal_id INTEGER NOT NULL REFERENCES rehearsal(rehearsal_id)
                 ON UPDATE CASCADE ON DELETE CASCADE,
    crew_id      INTEGER NOT NULL REFERENCES crew_member(crew_id)
                 ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (rehearsal_id, crew_id)
);

CREATE TABLE call_sheet (
    callsheet_id    INTEGER PRIMARY KEY,
    production_date DATE    NOT NULL,
    call_time       TIME    NOT NULL,
    rehearsal_id    INTEGER NOT NULL UNIQUE REFERENCES rehearsal(rehearsal_id)
                    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE attendance (
    attendance_id INTEGER     PRIMARY KEY,
    status        VARCHAR(10) NOT NULL
                  CHECK (status IN ('Present','Absent','Late','Excused')),
    rehearsal_id  INTEGER     NOT NULL UNIQUE REFERENCES rehearsal(rehearsal_id)
                  ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE sm_coord_scene_cue (
    cue_id   INTEGER NOT NULL REFERENCES cue(cue_id)
             ON UPDATE CASCADE ON DELETE CASCADE,
    scene_id INTEGER NOT NULL REFERENCES scene(scene_id)
             ON UPDATE CASCADE ON DELETE CASCADE,
    sm_id    INTEGER NOT NULL REFERENCES stage_manager(sm_id)
             ON UPDATE CASCADE ON DELETE RESTRICT,
    PRIMARY KEY (cue_id, scene_id)
);

CREATE TABLE light (
    cue_id          INTEGER PRIMARY KEY REFERENCES cue(cue_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
    stage_direction VARCHAR(100) NOT NULL
);

CREATE TABLE music (
    cue_id           INTEGER      PRIMARY KEY REFERENCES cue(cue_id)
                     ON UPDATE CASCADE ON DELETE CASCADE,
    title            VARCHAR(100) NOT NULL,
    duration_seconds INTEGER      NOT NULL CHECK (duration_seconds > 0)
);

CREATE TABLE sound (
    cue_id      INTEGER     PRIMARY KEY REFERENCES cue(cue_id)
                ON UPDATE CASCADE ON DELETE CASCADE,
    effect_type VARCHAR(50) NOT NULL
);

CREATE TABLE resource (
    resource_id         INTEGER     PRIMARY KEY,
    resource_type       VARCHAR(10) NOT NULL
                        CHECK (resource_type IN ('Prop','Costume','Equipment')),
    quantity            INTEGER     NOT NULL CHECK (quantity >= 0),
    condition           VARCHAR(10) NOT NULL
                        CHECK (condition IN ('New','Good','Fair','Poor')),
    availability_status VARCHAR(15) NOT NULL
                        CHECK (availability_status IN ('Available','Checked Out','Under Repair','Retired')),
    venue_id            INTEGER     NOT NULL REFERENCES venue(venue_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
    production_id       INTEGER     NOT NULL REFERENCES production(production_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
    vendor_id           INTEGER     NOT NULL REFERENCES vendor(vendor_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (resource_id, resource_type)
);

CREATE TABLE rehearsal_resource_checkout (
    rehearsal_id INTEGER NOT NULL REFERENCES rehearsal(rehearsal_id)
                 ON UPDATE CASCADE ON DELETE CASCADE,
    resource_id  INTEGER NOT NULL REFERENCES resource(resource_id)
                 ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (rehearsal_id, resource_id)
);

CREATE TABLE prop (
    resource_id   INTEGER     PRIMARY KEY,
    resource_type VARCHAR(10) NOT NULL DEFAULT 'Prop' CHECK (resource_type = 'Prop'),
    dimensions    VARCHAR(30) NOT NULL,
    FOREIGN KEY (resource_id, resource_type)
        REFERENCES resource(resource_id, resource_type)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE costume (
    resource_id   INTEGER     PRIMARY KEY,
    resource_type VARCHAR(10) NOT NULL DEFAULT 'Costume' CHECK (resource_type = 'Costume'),
    type          VARCHAR(20) NOT NULL,
    size          VARCHAR(3)  NOT NULL CHECK (size IN ('XS','S','M','L','XL')),
    FOREIGN KEY (resource_id, resource_type)
        REFERENCES resource(resource_id, resource_type)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE equipment (
    resource_id   INTEGER     PRIMARY KEY,
    resource_type VARCHAR(10) NOT NULL DEFAULT 'Equipment' CHECK (resource_type = 'Equipment'),
    serial_number VARCHAR(20) NOT NULL UNIQUE,
    power_req     INTEGER     NOT NULL CHECK (power_req >= 0),
    maint_date    DATE        NOT NULL,
    FOREIGN KEY (resource_id, resource_type)
        REFERENCES resource(resource_id, resource_type)
        ON UPDATE CASCADE ON DELETE CASCADE
);