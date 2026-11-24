# Anisble_PaloAlto_Bootstrap

This enables you to access Palo Alto devices via oob mgmt.</br>

1. From the macro excel spread sheet run the following command: - </br>
   python3 bootstrap_from_firewalls.py</br>

<img width="1192" height="753" alt="image" src="https://github.com/user-attachments/assets/27f1e2b5-787d-4638-a4dd-be4dccf35ae2" />

This will automatically create a bootstrap directory where the bootstrap files can be added to Paloalto firewall.

<img width="899" height="286" alt="image" src="https://github.com/user-attachments/assets/c1b747cb-2f8a-4eab-a361-eb8114b715d9" />

ls -l

<img width="979" height="156" alt="image" src="https://github.com/user-attachments/assets/f78bc5e2-93fa-4f13-b982-31042fe29ec4" />


cat PA-01.cfg 

2. Copy and paste the configuration onto paloalto firewall.

<img width="1124" height="880" alt="image" src="https://github.com/user-attachments/assets/0eb5d700-350b-4e2b-a4a3-d194351a0e20" />

3. Console to the Paloalto firewall.</>

<img width="1590" height="331" alt="image" src="https://github.com/user-attachments/assets/ec32d106-5b82-4d85-92bf-6430fb67f450" />

4. Copy and paste your configuration into the Paloalto console.</>
5. You will be prompted to enter a  password for the user(s) from the spreadsheet.

<img width="1016" height="493" alt="image" src="https://github.com/user-attachments/assets/f644bb33-dfd2-4b6a-a622-6ac26acb39e3" />

<img width="889" height="303" alt="image" src="https://github.com/user-attachments/assets/47c9fe4b-0f36-44cc-ba53-767968ce4daa" />


This will then commit and exit.
If a mistake or mismatch of password is generated just run the last command again.



   


