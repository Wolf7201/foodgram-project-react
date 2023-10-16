i_dict = {
    'абрикосовое варенье': {
        'amount': 10, 'measurement_unit': 'г'
    }
}

arr1 = ['абрикосовое варенье', 8, 'г']
arr2 = ['абрикосовое пюре', 8, 'г']

res_arr = [arr1, arr2]

for arr in res_arr:
    if arr[0] in i_dict:
        i_dict[arr[0]]['amount'] += arr[1]
    else:
        i_dict[arr[0]] = {
            'amount': arr[1], 'measurement_unit': arr[2]
        }

print(i_dict)
