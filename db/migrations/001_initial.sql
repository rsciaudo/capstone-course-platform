CREATE TABLE groups (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE users (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_id integer NOT NULL REFERENCES groups (id),
    name text NOT NULL,
    role text NOT NULL CHECK (role IN ('student', 'educator'))
);

CREATE TABLE courses (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    group_id integer NOT NULL REFERENCES groups (id),
    name text NOT NULL
);

CREATE TABLE modules (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_id integer NOT NULL REFERENCES courses (id),
    name text NOT NULL,
    position integer NOT NULL CHECK (position > 0),
    UNIQUE (course_id, position)
);

CREATE TABLE content_items (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    module_id integer NOT NULL REFERENCES modules (id),
    type text NOT NULL CHECK (type IN ('quiz', 'file', 'slide')),
    position integer NOT NULL CHECK (position > 0),
    UNIQUE (module_id, position)
);

CREATE TABLE course_enrollments (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id integer NOT NULL REFERENCES users (id),
    course_id integer NOT NULL REFERENCES courses (id),
    UNIQUE (user_id, course_id)
);

CREATE TABLE course_edit_grants (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id integer NOT NULL REFERENCES users (id),
    course_id integer NOT NULL REFERENCES courses (id),
    UNIQUE (user_id, course_id)
);

CREATE INDEX users_group_id_idx ON users (group_id);

CREATE INDEX courses_group_id_idx ON courses (group_id);

CREATE INDEX course_enrollments_course_id_idx ON course_enrollments (course_id);

CREATE INDEX course_edit_grants_course_id_idx ON course_edit_grants (course_id);
