// Person uniqueness constraints
CREATE CONSTRAINT person_id IF NOT EXISTS
  FOR (p:Person) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT person_whatsapp IF NOT EXISTS
  FOR (p:Person) REQUIRE p.whatsappId IS UNIQUE;

// Index for name-based lookups
CREATE INDEX person_name IF NOT EXISTS
  FOR (p:Person) ON (p.lastName, p.firstName);

// Place uniqueness
CREATE CONSTRAINT place_name IF NOT EXISTS
  FOR (pl:Place) REQUIRE pl.name IS UNIQUE;
