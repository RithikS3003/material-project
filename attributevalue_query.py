# queries.py

GENERATE_NOUN_ID = "SELECT noun_id FROM attri_value_mstr ORDER BY noun_id DESC LIMIT 1;"
# SQL queries for attribute_value_mstr table
GET_NOUNS = " SELECT noun_id, noun, isActive, abbreviation, description FROM attri_value_mstr ORDER BY noun_id;"

GET_NOUN_BY_ID = "SELECT noun_id, noun, isActive, abbreviation, description FROM attri_value_mstr WHERE noun_id = :noun_id;"

CREATE_NOUN = "INSERT INTO attri_value_mstr (noun_id, noun, abbreviation, description, isActive) VALUES (:noun_id, :noun, :abbreviation, :description, :isActive) RETURNING noun_id, noun, abbreviation, description, isActive;"

UPDATE_NOUN = "UPDATE attri_value_mstr SET noun = :noun, abbreviation = :abbreviation, description = :description,isActive = :isActive WHERE noun_id = :noun_id RETURNING noun_id, noun, abbreviation, description, isActive;"

DELETE_NOUN = "DELETE FROM attri_value_mstr WHERE noun_id = :noun_id;"
