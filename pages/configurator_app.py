from datetime import datetime
import time
import pandas as pd
import streamlit as st
from configurator_validators import PetConfValidator,TypeConfValidator,PersonConfValidator,conn,get_db_session
from sqlalchemy import text
from configurator import get_configurator

# Lookup dicts

columns_lookup = {
    "types" : "type_id,pet_type",
    "lut_address" : "owner_address",
    "pet" : "pet_id,pet_name"
}

ignored_fields = {
    "pet" : "is_stray",
    "types" : "has_age_range",
    "person" : ""
}

# Funtions

def safe_sql_identifier(name):
    return "".join(c for c in name if c.isalnum() or c in ['_','(',')'])

def get_table_columns(tableName: str):
    return list((conn.query(f"SELECT * from {tableName}",ttl="0m").to_dict()).keys())
    
def get_sql_type(data: str):
    if data.isdigit():
        return "INTEGER"
    if data.isdecimal():
        return "DECIMAL"
    if len(data) == 1:
        return "CHAR(1)"
    return "VARCHAR(" + str(len(data)) + ")"    

def add_column_to_table(tableName: str, columnName: str, columnType: str):
    with next(get_db_session()) as s:
        columnName = safe_sql_identifier(columnName)
        columnType = safe_sql_identifier(columnType)
        sql_command = f"ALTER TABLE {tableName} ADD COLUMN {columnName} {columnType}"
        s.execute(text(sql_command))
        s.commit()

def find_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

def get_column_and_value(tableName: str):
    if ',' in columns_lookup[tableName]:
        table = conn.query(f"SELECT {columns_lookup[tableName]} FROM {tableName}")
        columns = columns_lookup[tableName].split(',')
        result: dict = { columns[0] : {}}
        for key,value in table[columns[0]].items():
            result[columns[0]][value] = str(value) + ":" +table[columns[1]][key]
        return result    
    else:
        return conn.query(f"SELECT {columns_lookup[tableName]} FROM {tableName}").to_dict()

def insert_info(*args):
    if type(args[0]) is not str:
        raise TypeError(f"First argument must be a string, given type is {type(args[0])}")
    with next(get_db_session()) as s:
        try:
            if args[0] == "types":
                s.execute(
                    text('INSERT INTO types(pet_type,weight_range,height_range,age_range) VALUES(:pet_type,:weight_range,:height_range,:age_range);'),
                    {"pet_type" : args[1], "weight_range" : args[2], "height_range" : args[3], "age_range" : args[4]}
                )
            elif args[0] == "pet": 
                s.execute(
                    text('INSERT INTO pet(pet_name,type_id,age,owner_address) VALUES(:name,:id,:age,:owner_address)'),
                    {"name" : args[1], "id" : args[2], "age" : args[3], "owner_address": args[4]}
                )
            elif args[0] == "person":
                s.execute(
                    text('INSERT INTO person(name,pet_id,occupation,nickname) VALUES(:name,:pet,:occupation,:nickname)'),
                    {"name" : args[1], "pet" : args[2],  "occupation" : args[3], "nickname" : args[4]}
                )   
            else:
                raise TypeError(f"Given string is not a table name: {args[0]}") 
        finally:
            s.commit()

def info_exists(*args):
    with next(get_db_session()) as s:
        if args[0] == "pet":
            result = s.execute(
                text("SELECT COUNT(1) FROM pet WHERE pet_name=:name AND type_id=:type_id AND owner_address=:address"),
                {"name" : args[1], "type_id" : args[2], "address" : args[4]}
                ).fetchone()
            return result[0] > 0
        elif args[0] == "types":
            result = s.execute(
                text("SELECT COUNT(1) FROM types WHERE pet_type=:pet_type"),
                {"pet_type" : args[1], "weight_range" : args[2], "height_range" : args[3], "age_range" : args[4]}
                ).fetchone()
            return result[0] > 0
        elif args[0] == "person":
            result = s.execute(
                text("SELECT COUNT(1) FROM person WHERE name=:name AND pet_id=:pet_id AND occupation=:occupation AND nickname=:nickname"),
                {"name" : args[1], "pet_id" : args[2], "occupation" : args[3], "nickname" : args[4]}
                ).fetchone()
            return result[0] > 0

def format_labels(option):
    return option[1]

#Main Structure

pet_columns = get_table_columns("pet")
types_columns = get_table_columns("types")
person_columns = get_table_columns("person")
current_table = []


st.warning("New columns will be added, but no validation beyond type will be performed")

# Session State configuration

if 'configurator' not in st.session_state:
    conf = get_configurator()
    st.session_state.configurator = conf
else:
    conf = st.session_state.configurator

if 'flag_modify' not in st.session_state:
    st.session_state.flag_modify = False

if 'db_input' not in st.session_state:
    st.session_state.db_input = True

if 'current_table' not in st.session_state:
    st.session_state.current_table = ""

if 'validated' not in st.session_state:
    st.session_state.validated = False

if 'continue_pressed' not in st.session_state:
    st.session_state.continue_pressed = False

if 'insert_pressed' not in st.session_state:
    st.session_state.insert_pressed = False

if 'validated_model' not in st.session_state:
    st.session_state.validated_model = {}

selected_col = st.selectbox("Select a column",options=conf.keys())

st.write(conf[selected_col])

if conf[selected_col]["flag_modify"]:
    st.session_state.flag_modify = True
    st.write("You can modify the given information")
else:
    st.session_state.flag_modify = False
    st.write("You cannot modify the given information")

if conf[selected_col]["used_for_validation"]:
    st.write("Information will be validated")
else:
    st.write("Information won't be validated(be careful)")
    st.session_state.validated = False

if conf[selected_col]["used_for_db_input"]:
    st.write("Information will be inserted into the database")
    st.session_state.db_input = True
else:
    st.session_state.db_input = False
    st.write("Information won't be used for database input(you're safe)")

if conf[selected_col]["src_table_name"] == "pet":
    st.session_state.current_table = "pet"
    current_table = pet_columns
    if conf[selected_col]["sample"]["is_stray"]:
        st.write("Given pet is a stray, it has no owner's address")
    else:
        st.write("Given pet has an owner's address")

elif conf[selected_col]["src_table_name"] == "person":
    st.session_state.current_table = "person"
    current_table = person_columns

elif conf[selected_col]["src_table_name"] == "types":
    st.session_state.current_table = "types"
    current_table = types_columns
    if conf[selected_col]["sample"]["has_age_range"]:
        st.write("Given type should have an age range")
    else:
        st.write("Given type shouldn't have an age range") 



with st.container(border=True):
    if conf[selected_col]["used_for_validation"] and st.button("Validate"):
        flag_caught_exception: bool = False
        try:
            if st.session_state.current_table == "pet":
                model = PetConfValidator.model_validate(conf[selected_col]["sample"])
            elif st.session_state.current_table == "types":
                model = TypeConfValidator.model_validate(conf[selected_col]["sample"])
            elif st.session_state.current_table == "person":
                model = PersonConfValidator.model_validate(conf[selected_col]["sample"])
        except ValueError as e:
            errors = []
            for error in e.errors():
                error_entry = {
                    "message": error['msg'],
                    "value": error.get('input', None),
                }
                errors.append(error_entry)
            st.error(errors)
            if st.session_state.db_input:
                st.write("Information cannot be inserted into the database now(if not modified)")
                st.session_state.db_input = False
            flag_caught_exception = True
        if not flag_caught_exception:    
            st.success("Validated! Result:")
            st.write(model)

            if len(model.model_extra.keys()) > 0:
                st.write("Extra fields:")
                st.write(model.model_extra)

            st.session_state.validated_model = model.model_dump(by_alias=True)

            st.session_state.validated = True
            if conf[selected_col]["used_for_db_input"]:
                st.session_state.db_input = True

    if st.session_state.flag_modify == True:
        if not conf[selected_col]["used_for_validation"] and conf[selected_col]["used_for_db_input"]:
            st.session_state.db_input = True
        with st.expander("Modify"):
            copy: dict = {}
            for key,value in conf[selected_col]["sample"].items():
                copy[key] = value

            with st.container(border=True):
                for key,value in conf[selected_col]["sample"].items():
                    if key in current_table:
                        if key not in conf[selected_col]["sample"].values():
                            if type(value) == str:
                                copy[key] = st.text_input(
                                    f"Input a new {key}",
                                    value
                                )
                            elif type(value) == int:
                                copy[key] = st.number_input(
                                    f"Input a new {key}",
                                    value=value,
                                    min_value=0
                                )
                            elif type(value) == datetime:
                                copy[key] = st.date_input(
                                    f"input a new {key}",
                                    value = value
                                ) 
                        else:
                            table_name = find_key_by_value(conf[selected_col]["sample"],key)
                            index = table_name[len(table_name)-1]
                            table_name = "ref_table_name" + str(index)

                            column = "ref_table_column" + str(index)
                            table = get_column_and_value(conf[selected_col]["sample"][table_name])

                            item = st.selectbox(
                                f"Select a new {key}",
                                options=(table[conf[selected_col]["sample"][column]]).items(),
                                format_func=format_labels
                                )

                            if "id" in conf[selected_col]["sample"][column]:
                                copy[key] = item[0]
                            else:
                                copy[key] = item[1]
                    elif "ref_" not in key and key not in ignored_fields[st.session_state.current_table]:
                        st.write(f"An element you introduced, namely: {key}, does not have a respective column in the {st.session_state.current_table} table")
                        st.write("Would you like to add a new column?")
                        if st.button("Yes"):
                            add_column_to_table(st.session_state.current_table,key,get_sql_type(value))
                            
                        
            if st.button("Confirm changes"):
                if st.session_state.validated:
                    st.session_state.validated = False
                for key,value in copy.items():
                    conf[selected_col]["sample"][key] = value

    if st.session_state.db_input:
        if st.button("Insert to db"):
            st.session_state.insert_pressed = True
        if st.session_state.insert_pressed: 
            if not st.session_state.validated:
                st.warning("Warning! Information has not been validated. are you sure you want to continue?")
                if st.button("Continue"):
                    st.session_state.continue_pressed = True
                if st.session_state.continue_pressed:
                    if st.session_state.current_table == "pet":
                        if not info_exists("pet",conf[selected_col]["sample"]["pet_name"],conf[selected_col]["sample"]["type_id"],conf[selected_col]["sample"]["age"],conf[selected_col]["sample"]["owner_address"]):
                            with st.spinner("Petting the lil' guy... taking pictures... saving info..."):
                                time.sleep(5)
                            insert_info("pet",conf[selected_col]["sample"]["pet_name"],conf[selected_col]["sample"]["type_id"],conf[selected_col]["sample"]["age"],conf[selected_col]["sample"]["owner_address"])
                            st.success("Succesfully inserted pet!")
                        else:
                            st.error("That data already exists in the pet table")
                    elif st.session_state.current_table == "types":
                        if not info_exists("types",conf[selected_col]["sample"]["pet_type"],conf[selected_col]["sample"]["weight_range"],conf[selected_col]["sample"]["height_range"],conf[selected_col]["sample"]["age_range"]):
                            with st.spinner("Browsing for pics... searching for scratch spot... researching facts..."):
                                time.sleep(5)
                            insert_info("types",conf[selected_col]["sample"]["pet_type"],conf[selected_col]["sample"]["weight_range"],conf[selected_col]["sample"]["height_range"],conf[selected_col]["sample"]["age_range"])
                            st.success("Succesfully inserted pet type!")
                        else:
                            st.error("That data already exists in the types table")
                    elif st.session_state.current_table == "person":
                        if not info_exists("person",conf[selected_col]["sample"]["name"],conf[selected_col]["sample"]["pet_id"],conf[selected_col]["sample"]["occupation"],conf[selected_col]["sample"]["nickname"]):
                            with st.spinner("Finding person on social media... reading bio... requesting a follow..."):
                                time.sleep(5)
                            insert_info("person",conf[selected_col]["sample"]["name"],conf[selected_col]["sample"]["pet_id"],conf[selected_col]["sample"]["occupation"],conf[selected_col]["sample"]["nickname"])
                            st.success("Succesfully inserted person!")
                        else:
                            st.error("That data already exists in the person table")
                    st.session_state.continue_pressed = False
                    st.session_state.insert_pressed = False
            else:
                if st.session_state.current_table == "pet":
                    if not info_exists("pet",st.session_state.validated_model["pet_name"],st.session_state.validated_model["type_id"],st.session_state.validated_model["age"],st.session_state.validated_model["owner_address"]):
                        with st.spinner("Petting the lil' guy... taking pictures... saving info..."):
                            time.sleep(5)
                        insert_info("pet",st.session_state.validated_model["pet_name"],st.session_state.validated_model["type_id"],st.session_state.validated_model["age"],st.session_state.validated_model["owner_address"])
                        st.success("Succesfully inserted pet!")
                    else:
                        st.error("That data already exists in the pet table")
                elif st.session_state.current_table == "types":
                    if not info_exists("types",st.session_state.validated_model["pet_type"],st.session_state.validated_model["weight_range"],st.session_state.validated_model["height_range"],st.session_state.validated_model["age_range"]):
                        with st.spinner("Browsing for pics... searching for scratch spot... researching facts..."):
                            time.sleep(5)
                        insert_info("types",st.session_state.validated_model["pet_type"],st.session_state.validated_model["weight_range"],st.session_state.validated_model["height_range"],st.session_state.validated_model["age_range"])
                        st.success("Succesfully inserted pet type!")
                    else:
                        st.error("That data already exists in the types table")
                elif st.session_state.current_table == "person":
                    if not info_exists("person",st.session_state.validated_model["name"],st.session_state.validated_model["pet_id"],st.session_state.validated_model["occupation"],st.session_state.validated_model["nickname"]):
                        with st.spinner("Finding person on social media... reading bio... requesting a follow..."):
                            time.sleep(5)
                        insert_info("person",st.session_state.validated_model["name"],st.session_state.validated_model["pet_id"],st.session_state.validated_model["occupation"],st.session_state.validated_model["nickname"])
                        st.success("Succesfully inserted person!")
                    else:
                        st.error("That data already exists in the person table")
                st.session_state.continue_pressed = False
                st.session_state.insert_pressed = False

st.write("If you consider you are done modifying the configurator, you are welcome to submit the changes")
clicked = st.button("Submit")

if clicked:
    flat_data = []

    for col, details in conf.items():
        row = {
            "column_name": col,
            "flag_modify": details["flag_modify"],
            "used_for_validation": details["used_for_validation"],
            "used_for_db_input": details["used_for_db_input"],
            "src_table_name": details["src_table_name"]
        }
        sample = details["sample"]
        row.update(sample)
        flat_data.append(row)

    df = pd.DataFrame(flat_data)

    output_file_path = 'conf_input.xlsx'
    with pd.ExcelWriter(output_file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, index=False)

    st.write("Data has been written to ", output_file_path)