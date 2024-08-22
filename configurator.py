import pandas as pd
import openpyxl
conf = {
    "col1_pet" : {
        "flag_modify" : True,

        "used_for_validation" : True,

        "used_for_db_input" : True,

        "src_table_name" : "pet",
        
        "sample" : {
            "is_stray" : False,

            "ref_table_name1" : "lut_address",
            "ref_table_column1" : "owner_address",
            
            "ref_table_name2" : "types",
            "ref_table_column2" : "type_id",
            
            "pet_name" : "Gicu",
            "age" : 5,
            "type_id" : "24",
            "owner_address" : "Strada Normei nr.4",
            "gender": "M"
        }
    },

    "col2_pet" : {
        "flag_modify" : False,
        
        "used_for_validation" : True,

        "used_for_db_input" : False,

        "src_table_name" : "pet",
        
        "sample" : {
            "is_stray" : True,

            "ref_table_name1" : None,
            "ref_table_column1" : None,

            "ref_table_name2" : "types",
            "ref_table_column2" : "type_id",

            "pet_name" : "Buster",
            "age" : 7,
            "type_id" : "1",
            "owner_address" : "Strada Principala nr.43"
        }
    },

    "col3_pet" : {
        "flag_modify" : True,
        

        "used_for_validation" : False,

        "used_for_db_input" : True,

        "src_table_name" : "pet",
        
        "sample" : {
            "is_stray" : True,
            
            "ref_table_name1" : "lut_address",
            "ref_table_column1" : "owner_address",

            "ref_table_name2" : "types",
            "ref_table_column2" : "type_id",
            
            "pet_name" : "Maru",
            "age" : 3,
            "type_id" : "3",
            "owner_address" : "Strada Memorandului nr.9"
        }
    },

    "col4_type" : {
        "flag_modify" : True,

        "used_for_validation" : True,

        "used_for_db_input" : False,

        "src_table_name" : "types",

        "sample" : {
            "has_age_range" : True,
            "pet_type" : "octopus",
            "weight_range" : "1-10",
            "height_range" : "4-15",
            "age_range" : "5,10"
        }
    },

    "col5_type" : {
        "flag_modify" : False,

        "used_for_validation" : True,

        "used_for_db_input" : True,

        "src_table_name" : "types",

        "sample" : {
            "has_age_range" : False,
            "pet_type" : "cuckoo",
            "weight_range" : "0-2",
            "height_range" : "1-3",
            "age_range" : "3-4"
        }
    },

    "col6_type" : {
        "flag_modify" : True,

        "used_for_validation" : False,

        "used_for_db_input" : True,

        "src_table_name" : "types",

        "sample" : {
            "has_age_range" : False,
            "pet_type" : "cuckoo",
            "weight_range" : "0-2",
            "height_range" : "1-3",
            "age_range" : "3-5"
        }
    },

    "col7_person" : {
        "flag_modify" : True,

        "used_for_validation" : True,

        "used_for_db_input" : True,

        "src_table_name" : "person",

        "ref_table_name1" : "pet",
        "ref_table_column1" : "pet_id",

        "sample" : {
            "pet_id" : "1",
            "name" : "R2D2",
            "occupation" : "droid",
            "nickname" : "RustBucket"
        }
    },

    "col8_person" : {
        "flag_modify" : True,

        "used_for_validation" : False,

        "used_for_db_input" : False,

        "src_table_name" : "person",

        "ref_table_name1" : "pet",
        "ref_table_column1" : "pet_id",

        "sample" : {
            "pet_id" : "4",
            "name" : "Ionel",
            "occupation" : "engineer",
            "nickname" : "N/A"
        }
    },

    "col9_person" : {
        "flag_modify" : True,

        "used_for_validation" : True,

        "used_for_db_input" : True,

        "src_table_name" : "person",

        "ref_table_name1" : "pet",
        "ref_table_column1" : "pet_id",

        "sample" : {
            "pet_id" : "3",
            "name" : "Elena",
            "occupation" : "maid",
            "nickname" : "N/A",
            "hobby" : "gardener"
        }
    }
}

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

# Step 2: Create a pandas DataFrame
df = pd.DataFrame(flat_data)

# Step 3: Save the DataFrame to an Excel file
output_file_path = 'conf_output.xlsx'
df.to_excel(output_file_path, index=False)

print("Data has been written to", output_file_path)

def get_configurator():
    input_file_path = 'conf_input.xlsx'
    df = pd.read_excel(input_file_path)

    conf = {}

    for _, row in df.iterrows():
        col_name = row['column_name']
        del row['column_name']
        conf[col_name] = {
            "flag_modify": row["flag_modify"],
            "used_for_validation": row["used_for_validation"],
            "used_for_db_input": row["used_for_db_input"],
            "src_table_name": row["src_table_name"],
            "sample": {}
        }
    
        for key, value in row.items():
            if pd.notna(value) and key not in conf[col_name]:
                conf[col_name]["sample"][key] = value

    return conf