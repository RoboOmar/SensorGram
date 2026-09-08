from sqlalchemy import create_engine, text
engine = create_engine('postgresql://neondb_owner:npg_PrJzHfmQ15kU@ep-winter-feather-aeezkrbx-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require')
with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='comments';"))
    print([r[0] for r in res])
