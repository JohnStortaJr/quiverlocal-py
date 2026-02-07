**Use Cases**

*Setup*

- The first time the software is used, it needs to be configured with locations to store domains and certificates.
- The prerequisites need to be installed
- Apache and Maria should be installed
- Need to figure out how to manage the users and groups that should own Apache and Maria.
  -  Can they be installed within the user env separate from the root installation?
- If setup has already been run, Quiver should recognize that and not repeat steps
  -   What to do if Apache is already there? The Quiver install should not overwrite other configurations
  -   Does MariaDB have the same challenges
  -   Can tags be used to indicate if something is part of Quiver

*Cleanup*

- This is the option to completely remove the tool
- The idea is that Quiver should be able to return the system to the exact configuration that existed before it was installed
- There needs to be warnings if sites have been created as they will be removed.
- There needs to be two options available
  1) Remove everything. Maria, Apache, all prerequisite packages. The installation should track which prerequisite packages it had to install vs which were already there. Do not remove packages that Quiver did not install.
  2) Remove only the configurations that were part of the Quiver configuration

*Install*

- This can only be run if the Setup is completed
- This is a new WP installation with a new database
- Prompt user for core information
- When completed, the user should be provided with the URL for the site that they can click to complete the WP config within the site

*Import*

- This will use a WP installation that was exported from somewhere else
- Need to define what is needed for the import to work
  -  Both the WP folders and the database
- The user is prompted for information to define the local configuration
- Need to update links within the site (this might need to be done by the user afterward)
- When completed, the user is provided with the URL that will take them to their local site

*Secure*

- Add an SSH certificate to an existing site so that it can use HTTPs
- Update links accordingly
- Requires updates to Apache and the database
- Options need to exist to remove the security from the site also

*Certify*

- Setup the local system as a certificate authority
- Some of this will be about creating the certificate while then providing information and instructions that the user will need to perform separately

*Remove*

- Remove a site

