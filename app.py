#   streamlit run app.py
import random
import time
from pydantic import ValidationError
import streamlit as st
from app_validators import TypeModel,PetModel,PersonModel
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

st.set_page_config(
    page_title="PostGres - Streamlit linker",
    page_icon="👋",
)

st.sidebar.success("Select another page above.")

# PostGreSql Connection

conn = st.connection("postgresql", type="sql")
DATABASE_URL = "postgresql://postgres:1q2w3e@localhost/streamLitTest"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# General Functions

def query_table(tableName: str):
    if tableName == "types":
        return conn.query('SELECT type_id,pet_type,weight_range,height_range FROM types;', ttl="0m")
    elif tableName == "pet":
        return conn.query('SELECT pet_id,pet_name,t.pet_type,age FROM pet INNER JOIN types t ON t.type_id = pet.type_id', ttl="0m")
    elif tableName == "person":
        return conn.query('SELECT person_id,p.pet_name,name,occupation,nickname FROM person INNER JOIN pet p on p.pet_id = person.pet_id', ttl="0m")
    
def query_table_without_id(tableName: str):
    if tableName == "types":
        return conn.query('SELECT pet_type,weight_range,height_range FROM types;', ttl="0m")
    elif tableName == "pet":
        return conn.query('SELECT pet_name,t.pet_type,age FROM pet INNER JOIN types t ON t.type_id = pet.type_id', ttl="0m")
    elif tableName == "person":
        return conn.query('SELECT name,p.pet_name,occupation,nickname FROM person INNER JOIN pet p on p.pet_id = person.pet_id', ttl="0m")

def get_id(infoTable: dict, selectedItem: str):
    for key,value in infoTable.items():
        if value == selectedItem:
            return key

def update_item(*args):
    if type(args[0]) is not str:
        raise TypeError("First argument must be a string(table's name)")
    with next(get_db_session()) as s:
        try:
            if args[0] == "types":
                
                if len(args) != 5:
                    raise IndexError(f"Invalid number of arguments for types table update. Expected 5, given {len(args)}")    
                
                try:
                    model = TypeModel(pet_type=args[1],weight_range=str(args[2][0]) + '-' + str(args[2][1]),height_range=str(args[3][0]) + '-' + str(args[3][1]))
                except ValidationError as ex:
                    st.write(ex)
                    return
                
                s.execute(
                    text('UPDATE types SET pet_type = :pet, weight_range = :weight, height_range = :height WHERE pet_type = :original'),
                    {"pet" : model.pet_type, "weight" : model.weight_range, "height" : model.height_range, "original" : args[4]}
                )

            elif args[0] == "pet":
                
                if len(args) != 4:
                    raise IndexError(f"Invalid number of arguments for pet table update. Expected 4, given {len(args)}")
                
                try:
                    model = PetModel(pet_name=args[1],age=args[2])
                except ValidationError as ex:
                    st.write(ex)
                    return
                
                s.execute(
                    text('UPDATE pet SET pet_name = :name, age = :age WHERE pet_id = :original'),
                    {"name" : model.pet_name, "age" : model.age, "original" : args[3]}
                )

            elif args[0] == "person":
                
                if len(args) != 6:
                    raise IndexError(f"Invalid number of arguments for person table update. Expected 6, given {len(args)}")
                
                try:
                    model = PersonModel(pet_id=args[1],name=args[2],occupation=args[3],nickname=args[4])
                except ValidationError as ex:
                    st.write(ex)
                    return
                
                s.execute(
                    text('UPDATE person SET pet_id = :pet, name = :name, occupation = :occupation, nickname = :nickname WHERE person_id = :original'),
                    { "pet" : model.pet_id, "name" : model.name, "occupation" : model.occupation, "nickname" : model.nickname, "original" : args[5]}
                )
                
            else:
                raise TypeError(f"Given string is not a table name: {args[0]}")
        finally:
            s.commit()

def insert_info(*args):
    if type(args[0]) is not str:
        raise TypeError(f"First argument must be a string, given type is {type(args[0])}")
    with next(get_db_session()) as s:
        try:
            if args[0] == "types":
                if len(args) != 4:
                    raise IndexError(f"Invalid number of arguments for types table insert. Expected 4, gived {len(args)}")
                
                try:
                    model = TypeModel(pet_type=args[1],weight_range=str(args[2][0]) + '-' + str(args[2][1]),height_range=str(args[3][0]) + '-' + str(args[3][1]))
                except ValidationError as ex:
                    st.write(ex)
                    return
                
                s.execute(
                    text('INSERT INTO types(pet_type,weight_range,height_range) VALUES(:pet_type,:weight_range,:height_range);'),
                    {"pet_type" : model.pet_type, "weight_range" : model.weight_range, "height_range" : model.height_range}
                )
            elif args[0] == "pet":
                if len(args) != 4:
                    raise IndexError(f"Invalid number of arguments for pet table insert. Expected 4, given {len(args)}")
                
                try:
                    model = PetModel(pet_name=args[1],type_id=args[2],age=args[3])
                except ValidationError as ex:
                    st.write(ex)
                    return

                s.execute(
                    text('INSERT INTO pet(pet_name,type_id,age) VALUES(:name,:id,:age)'),
                    {"name" : model.pet_name, "id" : model.type_id, "age" : model.age}
                )
            elif args[0] == "person":
                if len(args) != 4:
                    raise IndexError(f"Invalid number of arguments for person table insert. Expected 5, given {len(args)}")

                try:
                    model = PersonModel(pet_id=args[1],name=args[2],occupation=args[3],nickname=args[4])
                except ValidationError as ex:
                    st.write(ex)
                    return

                s.execute(
                    text('INSERT INTO person(pet_id,name,occupation,nickname) VALUES(:pet,:name,:occupation,:nickname)'),
                    {"pet" : model.pet_id, "name" : model.name, "occupation" : model.occupation, "nickname" : model.nickname}
                )   
            else:
                raise TypeError(f"Given string is not a table name: {args[0]}") 
        finally:
            s.commit() 

def delete_item(tableName: str,selectedItem,currentDict: dict):
    with next(get_db_session()) as s:
        try:
            if tableName == "types":
                s.execute(
                    text('DELETE FROM types WHERE pet_type = :type'),
                    {"type" : selectedItem}
                )
                currentDict = query_table("types").to_dict()

            elif tableName == "pet":
                s.execute(
                    text('DELETE FROM pet WHERE pet_id = :pet'),
                    {"pet" : selectedItem}
                )
                currentDict = query_table("pet").to_dict()

            elif tableName == "person":
                s.execute(
                    text('DELETE FROM person WHERE person_id = :person'),
                    {"person" : selectedItem}
                )
                currentDict = query_table("person").to_dict()
            else:
                raise TypeError(f"Given string is not a tablename: {tableName}")
        finally:
            s.commit()

# Type Functions

def get_range(selectedIndex: int,info_table: dict,selectedRange: str) -> tuple[int,int]:
    weight_range_str = info_table[selectedRange][selected_index]
    return tuple(map(int, weight_range_str.split('-')))

def type_exists(pet: str):
    with next(get_db_session()) as s:
        result = s.execute(
            text('SELECT COUNT(1) FROM types WHERE pet_type = :pet'),
            { "pet" : pet}).fetchone()
        return result[0] > 0

# Pet Functions

def format_labels(option):
    return option[1]

# App structure

types_table = query_table("types").to_dict()
pets_table = query_table("pet").to_dict()

tab_person, tab_pet, tab_types, tab_shuffle = st.tabs([
    ":man-woman-boy: Person :man-girl-girl:",
    ":dog: Pet :cat:",
    ":rabbit::raccoon: Type(we don't judge) :frog::tiger:"])


with tab_person:
    st.header("Here's some tools to operate on the persons table")
    CRUD_option = tab_person.selectbox(
        "Select an operation:",
        ("Add person", "Modify person", "Delete person" )
    )
    persons_table = query_table("person").to_dict()

    if CRUD_option == "Add person":
        with st.form("add_person_form"):    
            person_name = st.text_input("Input your name",max_chars=20)

            pet_info = st.selectbox(
                "Select your lil' friend",
                placeholder="What's his name?",
                options=list(pets_table["pet_name"].items()),
                format_func=format_labels
            )
            col1, _, col2  = st.columns([1, 0.58, 1])

            with col1.popover("What's your occupation?"):
                person_occupation = st.text_input("Type here",max_chars=40)

            with col2.popover("Got a nickname? Mind sharing?"):
                person_nickname = st.text_input("Surprise us",max_chars=20,value="N/A")

            submitted = st.form_submit_button("Add Person")
            if submitted:
                insert_info("person",pets_table["pet_id"][pet_info[0]],person_name,person_occupation,person_nickname)
                with st.spinner('Browsing social media... searching for occupation... admiring nickname...'):
                    time.sleep(5)
                st.success('Person added!')
                st.balloons()
                persons_table = query_table("person").to_dict()

    elif CRUD_option == "Modify person":
        selected_person = st.selectbox(
            "Select a person to modify(how'd u get it wrong the first time?)",
            options=list(persons_table["name"].items()),
            format_func=format_labels
        )


        with st.form("modify_person_form"):

            col1, _, col2 = st.columns([1, 0.1, 1])

            col3, _, col4 = st.columns([1, 0.1, 1]) 

            _, col5, _ = st.columns([1.3, 1, 1])

            with col1.expander("Modify name"):
                new_name = st.text_input(
                    "Chage the name(won't fix your ID though...)",
                    value=selected_person[1]
                )

            with col2.expander("Change pet"):
                new_pet = st.selectbox(
                    "Select your ACTUAl pet",
                    placeholder="How'd you get it wrong the first time...",
                    options=list(pets_table["pet_name"].items()),
                    index = get_id(pets_table["pet_name"],persons_table["pet_name"][selected_person[0]]),
                    format_func=format_labels
                )

            with col3.expander("Modify occupation"):
                new_occupation = st.text_input(
                    "Change occupation(that seems shady)",
                    value = persons_table["occupation"][selected_person[0]]
                )

            with col4.expander("Modify nickname"):
                new_nickname = st.text_input(
                    "Change nickname",
                    value = persons_table["nickname"][selected_person[0]]
                )
            submitted = col5.form_submit_button("Submit changes")
            if submitted:
                update_item("person",pets_table["pet_id"][new_pet[0]],new_name,new_occupation,new_nickname,persons_table["person_id"][selected_person[0]])
                st.success("The person's information has been updated succesfully")
                persons_table = query_table("person").to_dict()

    elif CRUD_option == "Delete person":    
         with st.form("delete_person_form"):
            selected_person = st.selectbox(
                "Select the person you want to delete(what'd they do to you?)",
                options=list(persons_table["name"].items()),
                placeholder="Choose the poor soul",
                format_func=format_labels,
                index = None
            )

            submitted = st.form_submit_button("Been good knowing them")
            if submitted and selected_person != None:
                delete_item("person",persons_table["person_id"][selected_person[0]],persons_table)
                st.success("Person has been deleted succesfully(it's been good knowing them)")
    
    with st.expander("Show persons"):
        st.table(query_table_without_id("person"))
    


with tab_pet:
    st.header("Here's some tools to operate on the pet table(adorable!)")
    CRUD_option = tab_pet.selectbox(
        "Select an operation to manage the pets",
        ("Add pet(welcome lil guy!)", "Modify pet(what's wrong with him?)", "Delete pet(why?)" )
    )

    if CRUD_option == "Add pet(welcome lil guy!)":
        type_select = st.selectbox(
            "Select a pet type",
            options=list(types_table["pet_type"].values()),
            placeholder= "Type here...",
            index = None
        )   
        with st.form("add_pet_form"):
            pet_name = st.text_input("Input pet's name", max_chars = 15,placeholder="What's your good friend going to be called?")

            type_Id = get_id(types_table["pet_type"],type_select)

            age_value = st.number_input(
                "Select your pet's age",
                0, 100, 0
                )
            
            submitted = st.form_submit_button("Submit")
            if submitted:
                insert_info("pet",pet_name,types_table["type_id"][type_Id],age_value)
                with st.spinner('Noting down name... analyzing age... seeking species...'):
                    time.sleep(5)
                st.success('Pet added!')
                st.balloons()
                pets_table = query_table("pet").to_dict()
    
    elif CRUD_option == "Modify pet(what's wrong with him?)":
        selected_pet = st.selectbox(
            "Select the pet you want to modify",
            options=list(pets_table["pet_name"].items()),
            placeholder="Choose a friend!",
            format_func=format_labels
        )

        st.write("Sadly you cannot edit your pet's type, altough there's no way you could mismatch that...right?")
        
        with st.form("modify_pet_form"):
    
            with st.popover("Change pet's name"):
                pet_name = st.text_input("Select a new name:",value=selected_pet[1])

            with st.popover("Change pet's age"):
                pet_age = st.slider(
                    "Choose a new age(how can you forget your pet's age?)",
                    0, 100,
                    pets_table["age"][selected_pet[0]]
                )

            submitted = st.form_submit_button("Submit")
            if submitted:
                update_item("pet",pet_name,pet_age,int(pets_table["pet_id"][selected_pet[0]]))
                st.success("Pet information has been updated(and correct now, hopefully)")
                pets_table = query_table("pet").to_dict()

    elif CRUD_option == "Delete pet(why?)":
        with st.form("delete_pet_form"):
            selected_pet = st.selectbox(
                "Select the pet you want to delete(sad)",
                options=list(pets_table["pet_name"].items()),
                placeholder="Choose a friend!",
                format_func=format_labels
            )

            submitted = st.form_submit_button("Farewell, friend")
            if submitted:
                delete_item("pet",pets_table["pet_id"][selected_pet[0]],pets_table)
                st.success("Pet has left this mortal plane...(the database, we mean, he's still alive...right?)")

    with st.expander("Show pets"):
        st.table(query_table_without_id("pet"))
            

with tab_types:
    
    tab_types.header("Here's some tools to operate on the pet type table")

    CRUD_option = tab_types.selectbox(
    "Please select an operation",
    ("Add type", "Modify type", "Delete type...why would you?:["),) 

    if CRUD_option == "Add type":
        with st.form("add_type_form"):
            type_box = st.text_input("Input an animal species",max_chars=15,placeholder="Type here...")

            weight_values = st.slider(
            "Select the animal's weight range(kg)",
            0, 100, (10, 25))

            height_values = st.slider(
            "Select the animal's height range(cm)",
            0, 300, (50, 80))

            submitted = st.form_submit_button("Submit")
            if submitted:
                if not type_exists(type_box):
                    insert_info("type",type_box,weight_values,height_values)
                    with st.spinner('Writing down... analyzing... seeking cute pics...'):
                        time.sleep(5)
                    st.success('Done!')
                    st.balloons()
                else:
                    st.error('That pet already exists(and it is really cute)')
        
    
    elif CRUD_option == "Modify type":
        
        selected_type = tab_types.selectbox("Select an animal type to modify", options=list(types_table["pet_type"].values()), placeholder= "Type here...")

        with st.form("modify_type_form"):
            new_type = st.text_input("Change the animal's type",selected_type)

            selected_index = get_id(types_table["pet_type"],selected_type)

            new_weight = st.slider(
                "Edit the animal's weight range(kg, obviously)",
                0, 100, (get_range(selected_index,types_table,"weight_range"))
            )
            new_height = st.slider(
                "Edit the animal's height range(cm, as you would expect)",
                0, 300, (get_range(selected_index,types_table,"height_range"))
            )

            submitted = st.form_submit_button("Submit")
            if submitted:
                update_item("types",new_type,new_weight,new_height,selected_type)
                st.success("Type has been modified(hooray... you got some information wrong the first time...)")
                types_table = query_table("types").to_dict()

    elif CRUD_option == "Delete type...why would you?:[":
        with st.form("delete_type_form"):
            selected_type = st.selectbox("Select an animal type to delete(say goodbye)", options=list(types_table["pet_type"].values()), index = None, placeholder= "Search the poor thing's name...")

            submitted = st.form_submit_button("Delete(why?)")
            if submitted:
                delete_item("types",selected_type,types_table)
                st.success("That type of pet has been deleted(we will miss him)")
    
    with st.expander("Show types"):
        st.table(query_table_without_id("types"))
