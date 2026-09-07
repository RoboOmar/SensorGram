from sqlalchemy import create_engine, text
from backend.database import engine

def migrate():
    with engine.connect() as conn:
        print("Adding parent_comment_id to comments...")
        try:
            conn.execute(text("ALTER TABLE comments ADD COLUMN parent_comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE;"))
            conn.commit()
            print("Successfully added parent_comment_id.")
        except Exception as e:
            print(f"Error (maybe already exists?): {e}")
            conn.rollback()

        print("Creating comment_likes table...")
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comment_likes (
                id SERIAL PRIMARY KEY,
                robot_id INTEGER NOT NULL REFERENCES robots(id) ON DELETE CASCADE,
                comment_id INTEGER NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                UNIQUE(robot_id, comment_id)
            );
            """))
            conn.commit()
            print("Successfully created comment_likes.")
        except Exception as e:
            print(f"Error creating comment_likes: {e}")
            conn.rollback()

if __name__ == '__main__':
    migrate()
