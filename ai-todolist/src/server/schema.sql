
    DROP TABLE IF EXISTS tasks;
    
    CREATE TABLE tasks (
        id TEXT PRIMARY KEY,
        text TEXT NOT NULL,
        category TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        deleted INTEGER NOT NULL DEFAULT 0
    );
    