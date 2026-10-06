import sqlite3, json, uuid
from pathlib import Path

SCHEMA_VERSION="1.2"

class Store:
    def __init__(self, path="sonny.db"):
        self.path=path
        self.db=sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self._schema()

    def _schema(self):
        self.db.executescript('''
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            goal TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planning',
            state_version INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS memories(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            value TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            version INTEGER NOT NULL,
            source_event TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        CREATE TABLE IF NOT EXISTS memory_events(
            id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            event TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS actions(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            action_text TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PROPOSED',
            source_response_id TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
                CREATE TABLE IF NOT EXISTS traces(
            response_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            host_model TEXT NOT NULL,
            sonny_core_version TEXT NOT NULL,
            project_state_version INTEGER NOT NULL,
            answer_state TEXT NOT NULL,
            memory_write_proposed INTEGER NOT NULL DEFAULT 0,
            next_action_generated INTEGER NOT NULL DEFAULT 0,
            latency_ms INTEGER NOT NULL DEFAULT 0,
            estimated_cost REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS messages(
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            response_id TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        CREATE INDEX IF NOT EXISTS idx_messages_project_created
        ON messages(user_id,project_id,created_at);
        ''')
        self.db.commit()

    def uid(self):
        return str(uuid.uuid4())

    def create_user(self,name):
        i=self.uid()
        self.db.execute("INSERT INTO users VALUES(?,?)",(i,name))
        self.db.commit()
        return i

    def create_project(self,u,name,goal):
        i=self.uid()
        self.db.execute(
            "INSERT INTO projects(id,user_id,name,goal) VALUES(?,?,?,?)",
            (i,u,name,goal)
        )
        self.db.commit()
        return i

    def project(self,u,p):
        r=self.db.execute(
            "SELECT * FROM projects WHERE id=? AND user_id=?",
            (p,u)
        ).fetchone()
        return dict(r) if r else None

    def memories(self,u,p):
        return [
            dict(x) for x in self.db.execute(
                "SELECT * FROM memories WHERE user_id=? AND project_id=? AND status='CONFIRMED'",
                (u,p)
            )
        ]

    def propose_memory(self,u,p,value,typ="fact"):
        if not self.project(u,p):
            return None
        i=self.uid()
        self.db.execute(
            "INSERT INTO memories(id,user_id,project_id,value,type,status,version,source_event) VALUES(?,?,?,?,?,'PROPOSED',1,?)",
            (i,u,p,value,typ,"explicit_user_statement")
        )
        self.db.commit()
        return i

    def confirm_memory(self,u,p,m):
        cur=self.db.execute(
            "UPDATE memories SET status='CONFIRMED' WHERE id=? AND user_id=? AND project_id=? AND status='PROPOSED'",
            (m,u,p)
        )
        self.db.commit()
        return cur.rowcount==1

    def correct_memory(self,u,p,m,value):
        old=self.db.execute(
            "SELECT * FROM memories WHERE id=? AND user_id=? AND project_id=? AND status='CONFIRMED'",
            (m,u,p)
        ).fetchone()

        if not old:
            return None

        self.db.execute(
            "UPDATE memories SET status='CORRECTED' WHERE id=?",
            (m,)
        )

        n=self.uid()

        self.db.execute(
            "INSERT INTO memories(id,user_id,project_id,value,type,status,version,source_event) VALUES(?,?,?,?,?,'CONFIRMED',?,?)",
            (n,u,p,value,old['type'],old['version']+1,f"correction:{m}")
        )

        self.db.execute(
            "INSERT INTO memory_events(id,memory_id,event,old_value,new_value) VALUES(?,?,?,?,?)",
            (self.uid(),m,'CORRECTED',old['value'],value)
        )

        self.db.execute(
            "UPDATE projects SET state_version=state_version+1 WHERE id=?",
            (p,)
        )

        self.db.commit()
        return n

    def delete_memory(self,u,p,m):
        cur=self.db.execute(
            "UPDATE memories SET status='DELETED' WHERE id=? AND user_id=? AND project_id=?",
            (m,u,p)
        )

        self.db.execute(
            "UPDATE projects SET state_version=state_version+1 WHERE id=? AND user_id=?",
            (p,u)
        )

        self.db.commit()
        return cur.rowcount==1

    def actions(self,u,p):
        return [
            dict(x) for x in self.db.execute(
                "SELECT * FROM actions WHERE user_id=? AND project_id=?",
                (u,p)
            )
        ]

    def trace(self,rid,u,p,host,core,state,answer,memory_proposed,next_action,latency,cost):
        self.db.execute(
            "INSERT INTO traces VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                rid,u,p,host,core,state,answer,
                int(memory_proposed),
                int(next_action),
                latency,cost
            )
        )
        self.db.commit()

    def propose_action(self,u,p,text,reason="Sonny next step",response_id=None):
        if not self.project(u,p):
            return None

        i=self.uid()

        self.db.execute(
            "INSERT INTO actions(id,user_id,project_id,action_text,reason,source_response_id) VALUES(?,?,?,?,?,?)",
            (i,u,p,text,reason,response_id)
        )

        self.db.commit()
        return i

    def action_feedback(self, u, p, a, status):
        if status not in {
            "ACCEPTED",
            "EDITED",
            "REJECTED",
            "DEFERRED",
            "COMPLETED"
        }:
            return False

        cur = self.db.execute(
            """
            UPDATE actions
            SET status=?
            WHERE id=?
              AND user_id=?
              AND project_id=?
            """,
            (status, a, u, p)
        )

        self.db.commit()

        return cur.rowcount > 0


    def add_message(
        self,
        u,
        p,
        role,
        content,
        response_id=None
    ):
        if role not in {"user", "assistant"}:
            return None

        if not self.project(u, p):
            return None

        i = self.uid()

        self.db.execute(
            """
            INSERT INTO messages(
                id,
                user_id,
                project_id,
                role,
                content,
                response_id
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                i,
                u,
                p,
                role,
                content,
                response_id
            )
        )

        self.db.commit()

        return i


        def messages(
        self,
        u,
        p,
        limit=20
    ):
        rows = self.db.execute(
            """
            SELECT *
            FROM (
                SELECT rowid AS message_order, *
                FROM messages
                WHERE user_id=?
                  AND project_id=?
                ORDER BY rowid DESC
                LIMIT ?
            )
            ORDER BY message_order ASC
            """,
            (
                u,
                p,
                limit
            )
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]
