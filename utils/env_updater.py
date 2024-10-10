def update_env_variable(env_file_path, var_name, new_value):
    with open(env_file_path, 'r') as file:
        lines = file.readlines()

    with open(env_file_path, 'w') as file:
        for line in lines:
            if line.startswith(f'{var_name}='):
                file.write(f'{var_name}={new_value}\n')
            else:
                file.write(line)
