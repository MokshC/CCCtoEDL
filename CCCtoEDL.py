# Moksh

import argparse
import os
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

def write_output_edl(output_path, edl_content, ccc_dict):
    # Prepare the output file contents
    output_content = []
    for line in edl_content:
        if line.startswith('TITLE:'):
            output_content.append('TITLE: /ads/wk13/01_assists/Moksh/zz-exports/260204_cdl/OUTPUT.edl\n')
        elif line.startswith('FCM:'):
            output_content.append(line)
        elif line.strip().isdigit():  # Detecting EDL entries based on line starting with a number
            entry_number = line.split()[0]
            ccc_values = ccc_dict.get(entry_number)
            if ccc_values:
                slope, offset, power, saturation = ccc_values
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

# Searches for CCC files in given directory and returns list of their paths
def find_ccc_files(cccDir):
    # Define the search pattern
    pattern = "*.ccc"
    found_paths = []

    # Loop through the specified directory and its subdirectories
    for root, dirs, files in os.walk(cccDir):
        for filename in fnmatch.filter(files, pattern):
            found_paths.append(os.path.join(root, filename))
    
    return found_paths

def process_edl(edl, cccDir):
    # Example function to process the EDL file and CCC files
    print(f"Processing EDL: {edl}")
    print(f"Using CCC Directory: {cccDir}")
    
    cccList = find_ccc_files(cccDir)
    
    # Let's mock that we're creating an output file
    output_file = f"{os.path.splitext(edl)[0]}_cdl.edl"
    
    with open(output_file, 'w') as f:
        f.write("This is a mock CDL output.\n")
    
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
