# Moksh

import argparse
import os
import re
import glob
import fnmatch
import xml.etree.ElementTree as ET

def read_ccc_file(ccc_path):
    # Read the Color Correction Collection (CCC) file and extract the values needed
    tree = ET.parse(ccc_path)
    root = tree.getroot()
    
    # Extracting SOP values
    sop_node = root.find('.//SOPNode')
    slope = sop_node.find('Slope').text.split()
    offset = sop_node.find('Offset').text.split()
    power = sop_node.find('Power').text.split()
    
    # Extracting Saturation value
    sat_node = root.find('.//SatNode')
    saturation = sat_node.find('Saturation').text.strip()
    
    return slope, offset, power, saturation

def read_edl_file(edl_path):
    # Read the initial EDL file and return its contents
    with open(edl_path, 'r') as file:
        content = file.readlines()
    return content



# Function to read the EDL file and extract event numbers and corresponding file names
def extract_event_mapping(edl_path):
    event_mapping = {}
    edl_file = read_edl_file(edl_path)
    for line in edl_file:
        # Look for lines that start with numbers (event lines)
        match = re.match(r'(\d{3})\s+(\S+)', line)
        if match:
            event_number = match.group(1)  # Get the event number (first group)
            file_name = match.group(2)      # Get the file name (second group)
            
            # Remove any extension (if present) for matching with CCC files
            base_name = os.path.splitext(file_name)[0]
            event_mapping[event_number] = base_name

    return event_mapping

# Searches for CCC files in the given directory and returns a dictionary with event numbers and their corresponding paths
def find_ccc_files(cccDir, edl_path):
    # Extract mapping from the EDL
    event_mapping = extract_event_mapping(edl_path)
    pattern = "*.ccc"
    found_paths = {}

    # Loop through the specified directory and its subdirectories
    for root, dirs, files in os.walk(cccDir):
        for filename in fnmatch.filter(files, pattern):
            # Extract the base filename without the ".ccc" extension
            base_name = os.path.splitext(filename)[0]

            # Loop through the event mapping to find matches
            for event_number, event_base_name in event_mapping.items():
                if event_base_name == base_name:
                    found_paths[event_number] = os.path.join(root, filename)
                    break  # Stop after finding the first match

    return found_paths

def write_output_edl(output_path, edl_content, ccc_dict):
    # Prepare the output file contents
    output_content = []
    for line in edl_content:
        if line.startswith('TITLE:'):
            output_content.append(line)
        elif line.startswith('FCM:'):
            output_content.append(line)
        elif line.strip().isdigit():  # Detecting EDL entries based on line starting with a number
            entry_number = line.split()[0]
            ccc_path = ccc_dict.get(entry_number)
            if ccc_path:
                slope, offset, power, saturation = read_ccc_file(ccc_path)
                new_line = line
                new_line += f"*ASC_SOP ({' '.join(map(lambda x: f'{float(x):.6f}', slope))})"
                new_line += f"({ ' '.join(map(lambda x: f'{float(x):.6f}', offset))})"
                new_line += f"({ ' '.join(map(lambda x: f'{float(x):.6f}', power))})\n"
                new_line += f"*ASC_SAT {float(saturation):.6f}\n"
                output_content.append(new_line)
            else:
                output_content.append(line)  # If no match found, just append the original line
        else:
            output_content.append(line)  # Append other lines unchanged

    # Write to the output EDL file
    with open(output_path, 'w') as file:
        file.writelines(output_content)

def process_edl(edl, cccDict):
    # Example function to process the EDL file and CCC files
    print(f"Processing EDL: {edl}")
    print(f"Using CCC Directory: {cccDir}")
    
    output_file = f"{os.path.splitext(edl)[0]}_cdl.edl"
    
    write_output_edl(output_file, read_edl_file(edl), cccDict)
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Converts EDL and CCCs to EDL with CDL values.')
    parser.add_argument('--edl', type=str, required=True, help='Input EDL file')
    parser.add_argument('--cccdir', type=str, required=True, help='Directory with CCC files')
    
    args = parser.parse_args()
    
    # Expand glob patterns for cccdir and search for cccs
    print("Searching for CCCs in", str(glob.glob(args.cccdir)))
    ccc_files = find_ccc_files(glob.glob(args.cccdir))
    
    if len(ccc_files) < 1:
        print("No CCC files found in the specified directory.")
        return
    
    output = process_edl(args.edl, ccc_files)
    print(f"Generated EDL CDL: {output}")

if __name__ == '__main__':
    main()
