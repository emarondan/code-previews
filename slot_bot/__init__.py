import tools
import sys
import requests
import config
import datetime

if __name__ == '__main__':
    '''
    This function takes 4 parameters to run. 
    id, username, password, proxy
    It plays the slot until the balance is above 250 or below 50
    '''
    try:
        if len(sys.argv) == 5:
            instance_dict = {
                'id' : sys.argv[1],
                'username' : sys.argv[2],
                'password' : sys.argv[3],
                'proxy' : sys.argv[4]}
        else:
            print('Wrong number of parameters')
            raise
    
        proxy_values = instance_dict['proxy'].split(':')
        proxy_user = proxy_values[2]
        proxy_password = proxy_values[3]
        proxy_host = proxy_values[0]
        proxy_port = proxy_values[1]

        # change status to running (1)
        print('Changing instance status to running(1)')
        url = "http://{}/change-instance-status?id={}&new_status={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_dict['id'], 1)
        
        response = requests.request("GET", url)

        # start playing
        tools_obj = tools.MainTools()
        v_display = tools_obj.create_display()
        driver = tools_obj.create_driver(proxy_host,proxy_port,proxy_user,proxy_password)
        loged_in = False
        for retry in range(5):
            try:
                loged_in = tools_obj.login(driver, instance_dict['username'], instance_dict['password'])
                break
            except:
                print(f'Error, Retrying login procedure ({retry + 1})')
                continue
        initialized = False
        done = False
        if loged_in:
            initialized = tools_obj.initialize_game(driver)
        if initialized:
            done, final_balance = tools_obj.play_game(driver, instance_dict['id'])
            if final_balance < 50:
                print('Mark this instance for cashback')
                # mark instance for cashback_wait (3)
                url = "http://{}/change-instance-status?id={}&new_status={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_dict['id'], 3)
                response = requests.request("GET", url)
            elif final_balance >= 290:
                print('Mark this instance as win')
                # send mail and mark as win (2)
                # TODO send mail
                url = "http://{}/change-instance-status?id={}&new_status={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_dict['id'], 2)
                response = requests.request("GET", url)
        driver.quit()
        if v_display:
            v_display.stop()
        sys.exit()

    except Exception as e:
        print(e)
        # update error + screenshot on database
        # take screenshot with pyautogui
        try:
            import pyautogui
            # TODO revisar si este import ocasiona algun error
            screenshot_name = datetime.datetime.now().strftime(f"{config.BOT_ERROR_PATH}{instance_dict['id']}-play-%d%m%Y%H%M%S.png")
            pyautogui.screenshot(screenshot_name)
        except:
            pass
        error = str(e)
        # update error field on database
        url = "http://{}/update-instance-field?id={}&field={}&value={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_dict['id'], 'last_error', f"'{error}'")
        requests.request("GET", url)
        # update screenshot field on database
        url = "http://{}/update-instance-field?id={}&field={}&value={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_dict['id'], 'last_screenshot', f"'{screenshot_name}'")
        requests.request("GET", url)
        # update status to 5 for this instance
        url = "http://{}/change-instance-status?id={}&new_status={}".format(config.API_HOST + ':' + str(config.API_PORT), instance_dict['id'], 5)
        requests.request("GET", url)
        try:
            driver.quit()
        except:
            pass
        try:
            v_display.stop()
        except:
            pass
        sys.exit()
        