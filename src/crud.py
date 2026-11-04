from db import run

# CREATE
def create_production(title, ptype, start_date, end_date, director_id, producer_id):
    sql = """INSERT INTO production
                 (production_id, title, type, start_date, end_date, director_id, producer_id)
             VALUES ((SELECT COALESCE(MAX(production_id), 0) + 1 FROM production),
                     %s, %s, %s, %s, %s, %s)"""
    _, n = run(sql, (title, ptype, start_date, end_date, director_id, producer_id))
    return n

# READ
def read_productions():
    sql = """SELECT production_id, title, type, start_date, end_date,
                    director_id, producer_id
             FROM production ORDER BY production_id"""
    rows, _ = run(sql, fetch=True)
    return rows

# UPDATE
def update_production(production_id, title, ptype, start_date, end_date,
                      director_id, producer_id):
    sql = """UPDATE production
             SET title = %s, type = %s, start_date = %s, end_date = %s,
                 director_id = %s, producer_id = %s
             WHERE production_id = %s"""
    _, n = run(sql, (title, ptype, start_date, end_date,
                     director_id, producer_id, production_id))
    return n

# DELETE
def delete_production(production_id):
    sql = "DELETE FROM production WHERE production_id = %s"
    _, n = run(sql, (production_id,))
    return n

# Helpers for the dropdowns in the UI (not part of the 4 CRUD operations)
def read_director_ids():
    rows, _ = run("SELECT director_id FROM director ORDER BY director_id", fetch=True)
    return [r[0] for r in rows]

def read_producer_ids():
    rows, _ = run("SELECT producer_id FROM producer ORDER BY producer_id", fetch=True)
    return [r[0] for r in rows]


if __name__ == "__main__":

    # 1. CREATE (uses the first existing director and producer)
    d = read_director_ids()[0]
    p = read_producer_ids()[0]
    print("Inserted rows:", create_production("Test Show", "Play","2026-12-01", "2026-12-31", d, p))

    # 2. READ
    #rows = read_productions()
    #for r in rows:
    #   print(r)
    #print("Rows returned:", len(rows))

    # 3. UPDATE (replace 99 with your test production's production_id)
    #d = read_director_ids()[0]
    #p = read_producer_ids()[0]
    #print("Updated rows:", update_production(99, "Test Show (Revised)", "Musical",
    #                                         "2026-12-05", "2027-01-05", d, p))

    # 4. DELETE (replace 99 with your test production's production_id)
    #print("Deleted rows:", delete_production(102))