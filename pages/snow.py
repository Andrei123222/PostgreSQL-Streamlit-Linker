from contextlib import contextmanager
import datetime
import time 
from pydantic import ValidationError
import snowflake.connector
import streamlit as st
from snow_validators import BrandModel,DeviceModel,StocksModel
from snowflake.snowpark import Session
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

connection_parameters = {
    "user" : st.secrets.snowflake.user,
    "password" : st.secrets.snowflake.password,
    "database" : st.secrets.snowflake.database,
    "account" : st.secrets.snowflake.account,
    "schema" : st.secrets.snowflake.schema
}

def get_db_session():
    if 'snowflake_conn' not in st.session_state:
        conn = snowflake.connector.connect(
            user=connection_parameters["user"],
            password=connection_parameters["password"],
            account=connection_parameters["account"],
            database=connection_parameters["database"],
            schema=connection_parameters["schema"]
        )
        st.session_state['snowflake_conn'] = conn
    return st.session_state['snowflake_conn']


def load_data(tableName: str):
    conn = get_db_session()
    if conn:
        with conn.cursor() as cursor:
            try:
                if tableName == "brand":
                    cursor.execute(f"SELECT * FROM {tableName}")
                    data = cursor.fetchall()
                    result: dict = { "brand_id" : {} , "name" : {}, "country" : {} , "active_since" : {}}
                    for i in range(len(data)):
                        result["brand_id"][str(i)] = data[i][0]
                        result["name"][str(i)] = data[i][1]
                        result["country"][str(i)] = data[i][2]
                        result["active_since"][str(i)] = data[i][3]

                elif tableName == "device":
                    cursor.execute(f"SELECT device_id,b.name,type,device.name,launch_date,device_price FROM {tableName} INNER JOIN brand b WHERE b.brand_id = {tableName}.brand_id")
                    data = cursor.fetchall()
                    result: dict = { "device_id" : {},"brand" : {}, "type" : {} , "name" : {}, "launch_date" : {}, "device_price" : {}}
                    for i in range(len(data)):
                        result["device_id"][str(i)] = data[i][0]
                        result["brand"][str(i)] = data[i][1]
                        result["type"][str(i)] = data[i][2]
                        result["name"][str(i)] = data[i][3]
                        result["launch_date"][str(i)] = data[i][4]
                        result["device_price"][str(i)] = int(data[i][5])

                elif tableName == "stocks":
                    cursor.execute(f"SELECT stock_id,d.name,supply_date,quantity,value FROM {tableName} INNER JOIN device d WHERE d.device_id = {tableName}.device_id")
                    data = cursor.fetchall()
                    result: dict = { "stock_id" : {},"device" : {}, "supply_date" : {} , "quantity" : {}, "value" : {}}
                    for i in range(len(data)):
                        result["stock_id"][str(i)] = data[i][0]
                        result["device"][str(i)] = data[i][1]
                        result["supply_date"][str(i)] = data[i][2]
                        result["quantity"][str(i)] = data[i][3]
                        result["value"][str(i)] = int(data[i][4])

                return result
            except Exception as e:
                st.error(f"Error loading data from table '{tableName}': {e}")
                return None
    else:
        st.error("Failed to establish a Snowflake session.")
        return None
    
def insert_data(*args):
    if type(args[0]) is not str:
        raise TypeError("First argument should be a string")
    conn = get_db_session()
    with conn.cursor() as cursor:
        try:
            if args[0] == "brand":
                if len(args) != 4:
                    raise IndexError(f"Incorrect number of arguments for brands table insert. Expected 4, got {len(args)}")

                try:
                    model = BrandModel(brand_name=args[1],country=args[2],active_since=args[3])
                except ValidationError as e:
                    st.write(e)
                    return 0

                cursor.execute(
                    'INSERT INTO brand(name,country,active_since) VALUES(%s,%s,%s)',
                    (model.brand_name, model.country, model.active_since)
                )
            elif args[0] == "device":
                if len(args) != 6:
                    raise IndexError(f"Incorrect number of arguments for device table insert. Expected 6, got {len(args)}")

                try:
                    model = DeviceModel(brand_id=args[1], device_type=args[2], device_name=args[3], launch_date=args[4], device_price=args[5])
                except ValidationError as e:
                    st.write(e)
                    return 0

                cursor.execute(
                    'INSERT INTO device(brand_id,type,name,launch_date,device_price) VALUES(%s,%s,%s,%s,%s) ',
                    (model.brand_id, model.device_type, model.device_name, model.launch_date, model.device_price)
                )
            elif args[0] == "stocks":
                if len(args) != 4:
                    raise IndexError(f"Incorrect number of arguments for stocks table insert. Expected 4, got {len(args)}")

                cursor.execute(
                    'SELECT device_price,device_id FROM device WHERE name=%s',(args[1])
                    )
                result = cursor.fetchone()
                price: float = result[0]
                id: int = result[1]
                
                try:
                    model = StocksModel(device_id=id, supply_date=args[2],quantity=args[3],value=args[3]*price)
                except ValidationError as e:
                    st.write(e)
                    return 0
                
                cursor.execute(
                    'INSERT INTO stocks (device_id,supply_date,quantity,value) VALUES(%s,%s,%s,%s)',
                    (model.device_id,model.supply_date,model.quantity,model.value)
                )
            else:
                raise TypeError("Given string is not a table name. It should be either 'brand', 'device' or 'stocks'")
        finally:
            cursor.close()
        conn.commit()

def update_data(*args):
    if type(args[0]) is not str:
        raise TypeError("Table name should be a string(and either brand,device or stocks)")
    conn = get_db_session()
    with conn.cursor() as cursor:
        try:
            if args[0] == "brand":
                if len(args) != 5:
                    raise IndexError(f"Incorrect number of arguments for brand table update. Expected 5, got {len(args)}")
                
                try:
                    model = BrandModel(brand_name=args[1],country=args[2],active_since=args[3])
                except ValidationError as e:
                    st.write(e)
                    return 0

                cursor.execute(
                    'UPDATE brand SET name=%s, country=%s, active_since=%s WHERE name=%s',
                    (model.brand_name, model.country, model.active_since, args[4])
                )

            elif args[0] == "device":
                if len(args) != 6:
                    raise IndexError(f"Incorrect number of arguments for device table update. Expected 6, got {len(args)}")
                
                try:
                    model = DeviceModel(device_type=args[1], device_name=args[2], launch_date=args[3], device_price=args[4])
                except ValidationError as e:
                    st.write(e)
                    return 0
                
                cursor.execute(
                    'UPDATE device SET type=%s,name=%s,launch_date=%s,device_price=%s WHERE name=%s',
                    (model.device_type,model.device_name,model.launch_date,model.device_price,args[5])
                )
            elif args[0] == "stocks":
                if len(args) != 6:
                    raise IndexError(f"Incorrect number of arguments for stocks table update. Expected 6, got {len(args)}")
                
                try:
                    model = StocksModel(supply_date=args[2],quantity=args[3],value=args[3]*args[4])
                except ValidationError as e:
                    st.write(e)
                    return 0
                cursor.execute(
                    'UPDATE stocks SET supply_date=%s,quantity=%s,value=%s WHERE stocks.device_id=%s',
                    (args[2],args[3],args[3]*args[4],args[5])
                )
            else:
                raise TypeError("Table name is incorrect. It should be either 'brand', 'device' or 'stocks'")
        finally:
            cursor.close()
        conn.commit()
            
def delete_data(tablename: str, data):
    conn = get_db_session()
    with conn.cursor() as cursor:
        try:
            if tablename == "brand":
                cursor.execute(
                    'DELETE FROM brand WHERE name=%s',
                    (data)
                )
            elif tablename == "device":
                cursor.execute(
                    'DELETE FROM device WHERE name=%s',
                    (data)
            )
            elif tablename == "stocks":
                cursor.execute(
                    'DELETE FROM stocks WHERE device_id=%s',
                    str(data)
                )
        finally:
            cursor.close()
        conn.commit()

def data_exists(tableName: str,data: str):
    conn = get_db_session()
    with conn.cursor() as cursor:
        try:
            if tableName == "brand":
                result = cursor.execute('SELECT COUNT(1) FROM brand WHERE name = %s',data).fetchone()
            elif tableName == "device":
                result = cursor.execute('SELECT COUNT(1) FROM device WHERE name = %s',data).fetchone()
            elif tableName == "stocks":
                result = cursor.execute('SELECT COUNT(1) FROM stocks WHERE device_id = %s',str(data)).fetchone()
        finally:
            cursor.close()

        return result[0]>0

def get_value_id(info_table: dict, value: str):
    for key,value in info_table.items():
            if value == value:
                return key  

def format_labels(option):
    return option[1]


tab_brand, tab_device, tab_stocks = st.tabs(["Brand", "Device", "Stocks"])

brands_table = load_data("brand")

with tab_brand:
    selected_option = st.selectbox(
        label="Choose an operation:",
        options=["Add brand", "Modify brand(not very professional of you)","Delete brand(bankruptcy, huh?)"]
    )

    if selected_option == "Add brand":
        with st.form("add_brand_form"):
            brand_name = st.text_input(
                "Choose your brand's name(this is the important step!)",
                placeholder="Type here...",
                max_chars=20
            )

            brand_country = st.text_input(
                "Choose your country of origin(if you don't want us to do it for you)",
                placeholder="You know which country you're in, right?",
                max_chars=20
            )

            brand_date = st.date_input("Since when has your brand been around?",)

            submitted = st.form_submit_button("Submit")
            if submitted:
                if not brand_name == "" and not brand_country == "":
                    if not data_exists("brand",brand_name):
                        if insert_data("brand",brand_name,brand_country,brand_date) != 0:
                            with st.spinner("Browsing the web...researching country...checking company's history..."):
                                time.sleep(3)
                            st.balloons()
                            st.success("Succesfully inserted the information")
                    else:
                        st.error("That name already exists! This doesn't seem legal(copyright and stuff)")
                else:
                    st.error("Name and country fields cannot be empty!")

    elif selected_option == "Modify brand(not very professional of you)":
        brand = st.selectbox(
            "Select a brand to modify",
            placeholder="This feels illegal...",
            options=brands_table["name"].items(),
            format_func=format_labels,
        )

        with st.form("modify_brand_form"):
            new_name = st.text_input(
                "Change the company name(don't steal one)",
                brand[1],
                max_chars=20
            )

            new_country = st.text_input(
                "Change the company's country(forgot the place you operate in?)",
                brands_table["country"][brand[0]],
                max_chars=20
            )

            new_date = st.date_input(
                "Change the company's creation date(been a while, huh)",
                brands_table["active_since"][brand[0]],
            )

            submitted = st.form_submit_button("Submit changes")
            if submitted:
                if update_data("brand",new_name,new_country,new_date,brand[1]):
                    st.success("Your brand has been updated succesfully")

    elif selected_option == "Delete brand(bankruptcy, huh?)":
        with st.container(border = True):
            bankrupted_brand = st.selectbox(
                "Select a brand to delete",
                placeholder="It was a good trip...",
                options=brands_table["name"].values(),
            )

            submitted = st.button("Bankrupt...")

            if submitted:
                delete_data("brand",bankrupted_brand)
                st.success("Brand has been deleted...so many years of work..")

    with st.expander("show table"):
        data_to_show = load_data("brand")
        del data_to_show["brand_id"]
        st.table(data_to_show)

devices_table = load_data("device")

with tab_device:
    selected_option = st.selectbox("Select an operation for the device table",["Add device","Modify device(it feels late for that but oh well)","Delete device(this'll be expensive)"])

    if selected_option == "Add device":
        device_brand = st.selectbox(
            "Select the brand to which this product is tied",
            options=brands_table["name"].items(),
            format_func=format_labels
        )

        with st.form("add_device_form"):
            device_type = st.text_input(
                "What type of device are we adding today?",
                placeholder="Type here..."
            )

            device_name = st.text_input(
                "Name your device(be creative)",
                placeholder="Something clever..."
            )

            device_launch = st.date_input(
                "When did you release this device?",
            )

            device_price = st.number_input(
                "How much is your device worth(think of your work!)",
                50, 10000, step = 10, value=1000
            )

            submitted = st.form_submit_button("Add")
            if submitted:
                if not data_exists("device",device_name):
                    if insert_data("device", brands_table["brand_id"][device_brand[0]],device_type,device_name,device_launch,device_price):
                        with st.spinner("Updating databases... making advertisements... finding sponsors..."):
                                time.sleep(3)
                        st.balloons()
                        st.success("Device inserted succesfully")
                elif data_exists("device",device_name):
                    st.error("A device with that name already exists. Don't shoot the messenger, just think of a better name")

    elif selected_option == "Modify device(it feels late for that but oh well)":
        selected_device = st.selectbox(
            "Select a device to modify",
            options=devices_table["name"].items(),
            format_func=format_labels
        )

        st.write("You are unable to change the brand, as this device is already property of the brand that created it(laws and stuff)")

        with st.form("modify_device_form"):
            with st.popover("Change type"):
                new_type = st.text_input(
                    "change the device's type",
                    value = devices_table["type"][selected_device[0]]
                )

            with st.popover("Change name"):
                new_name = st.text_input(
                    "Change the device's name(got new inspiration?)",
                    value=selected_device[1]
                )

            with st.popover("Change launch date"):
                new_launch = st.date_input(
                    "How come you got the date wrong? Better fix it if so",
                    value = devices_table["launch_date"][selected_device[0]]
                )
            with st.popover("Change price"):
                new_price = st.number_input(
                    "It became harder to produce, huh? Ah, inflation",
                    50, 10000, value = int(devices_table["device_price"][selected_device[0]]),
                    step=10
                )

            submitted = st.form_submit_button("Confirm changes")
            if submitted:
                if not data_exists("device",new_name):
                    if update_data("device",new_type,new_name,new_launch,new_price,selected_device[1]):
                        st.success("Your device has been updated succesfully(under legal terms, of course)")
                else:
                    st.error("Your inspiration was mismatched, as that name already exists")

    elif selected_option == "Delete device(this'll be expensive)":
        with st.container(border = True):
            device_to_delete = st.selectbox(
                "Select a device to delete(Buh bye stocks)",
                options=devices_table["name"].values(),
                )

            submitted = st.button("Delete")
            if submitted:
                delete_data("device",device_to_delete)
                st.success("The device has been deleted succesfully")
                
    with st.expander("show table"):
        data_to_show = load_data("device")
        del data_to_show["device_id"]
        st.table(data_to_show)

with tab_stocks:
    stocks_table = load_data("stocks")
    selected_option = st.selectbox(
            "Select an operation to perform on the stocks",
            options=["Add stock","Modify stock","Delete stock"]
        )

    if selected_option == "Add stock":
        selected_device = st.selectbox(
            "Select the device",
            options=devices_table["name"].items(),
            format_func=format_labels
            )
        
        with st.form("add_stock_form"):
            
            supply_date = st.date_input("Select the supply date",)

            quantity = st.number_input("Input the stock's quantity",0,1000,step=5)

            submitted = st.form_submit_button("Confirm")
            if submitted:
                if not data_exists("stocks",str(devices_table["device_id"][selected_device[0]])):
                    if insert_data("stocks",selected_device[1],supply_date,quantity):
                        with st.spinner("Dusting off warehouses... packaging graciously... employing mice-catchers(cats)..."):
                                time.sleep(3)
                        st.balloons()
                        st.success("Stock inserted succesfully")
                else:
                    st.error("A stock for that device already exists")

    elif selected_option == "Modify stock":
        selected_device = st.selectbox(
            "Select a device's stock to update",
            options=stocks_table["device"].items(),
            format_func=format_labels
            )

        device_id: int = get_value_id(devices_table["name"],selected_device[1])                                                                                                                         
                                                                                                                                                
        with st.form("modify_stock_form"):

            new_supply_date = st.date_input("Select the supply date", value=stocks_table["supply_date"][selected_device[0]])

            new_quantity = st.number_input("Change the quantity(sales or restock?)",0,1000,value=stocks_table["quantity"][selected_device[0]])

            submitted = st.form_submit_button("Submit changes")
            if submitted:
                if update_data("stocks",selected_device[1],new_supply_date,new_quantity,devices_table["device_price"][device_id],devices_table["device_id"][device_id]):
                    st.success("Stock was updated succesfully")

    elif selected_option == "Delete stock":
        with st.container(border=True):
            selected_device = st.selectbox(
                "Select a device's stock to delete(sold out or should we be worried?)",
                options=stocks_table["device"].values()
            )

            st.write(selected_device)

            device_id = get_value_id(devices_table["name"],selected_device)

            submitted = st.button("Delete")
            if submitted: 
                delete_data("stocks",devices_table["device_id"][device_id])
                st.success("Deleted succesfully!(hope it was a good sell, if it was one)")

        
    with st.expander("show table"):
        data_to_show = load_data("stocks")
        del data_to_show["stock_id"]
        st.table(data_to_show)