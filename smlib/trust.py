#!/usr/bin/python3

from smlib.core import *
from smlib.format import *
from smlib.info import *
from smlib.create import *
import json
import shutil
import random

def trustSite(localDatabase = quiverDB):
    keepRunning = True

    while keepRunning:
        #os.system('clear')
        print("")
        menuCounter = 0
        print(6 * "-" , "Installed Sites" , 6 * "-")

        siteFileList = sorted(os.listdir(localDatabase + "/sites"))

        siteList = []
        for i in siteFileList:
            menuCounter += 1

            if i.endswith(".json"):
                with open(quiverDB + "/sites/" + i, 'r') as inFile:
                    foundSite = json.load(inFile)
                    siteList.append(foundSite)
                    updateTablePrefix(foundSite)

                    if foundSite["isTrusted"]:
                        print(style.FAINT + str(menuCounter) + " " + foundSite["siteName"] + " ♥" + style.END)
                    else:
                        print(style.BOLD + str(menuCounter) + " " + foundSite["siteName"] + style.END )

        print("")
        print(style.BOLD + "0 " + style.END + "Back")    
        print(21 * "-")

        selection = int(getInput("Which site would you like to trust [0-" + str(menuCounter) + "]? ", True))

        if selection > len(siteList):
            print(background.BYELLOW + "Unknown selection" + background.END)
            continue
        elif selection == 0:
            return

        siteToTrust = siteList[selection-1].copy()

        if siteList[selection-1]["isTrusted"]:
            print(background.BYELLOW + siteList[selection-1]["siteName"] + " is already trusted" + background.END)
            confirmation = input("Do you wish to change the certificate used by this site [y/N]? ").strip()

            if (confirmation != "y") and (confirmation != "Y"): continue

        # Clear existing configuration except current key and certificate
        siteToTrust["certID"] = ""
        siteToTrust["certRequest"] = ""
        siteToTrust["certConfig"] = ""
        siteToTrust["certRootKey"] = ""
        siteToTrust["certRoot"] = ""

        selection = getInput("Do you already have a signed certificate you would like to use [y/N]? ")

        if (selection == "y") or (selection == "Y"):
            # Get the paths to the certificate files from the user
            siteToTrust = getCertificate(siteToTrust)
        else:
            siteToTrust = createNewCertificates(siteToTrust)

        #print(json.dumps(siteToTrust, indent=4))

        # Add the certificate paths to the Apache configuration
        addCertificate(siteToTrust)

        # Update the WordPress database to reflect the https URLs
        updateSiteValues(siteToTrust, "https")

        restartApache()

        # Mark this site as trusted and write the dictionary to the quiver database
        siteToTrust["isTrusted"] = True
        writeSiteConfig(siteToTrust)

        print("")
        print(style.BOLD + siteToTrust["siteName"] + style.END + " is now trusted " + style.END)
        print("Once the corresponding CA ROOT certificate is added to the local system, ")
        print("the site can be accessed using https://" + siteToTrust["domainName"] + style.END)


def untrustSite(localDatabase = quiverDB):
    keepRunning = True

    while keepRunning:
        print("")
        menuCounter = 0
        print(6 * "-" , "Installed Sites" , 6 * "-")

        siteFileList = sorted(os.listdir(localDatabase + "/sites"))

        siteList = []
        for i in siteFileList:
            menuCounter += 1

            if i.endswith(".json"):
                with open(quiverDB + "/sites/" + i, 'r') as inFile:
                    foundSite = json.load(inFile)
                    siteList.append(foundSite)
                    updateTablePrefix(foundSite)

                    if foundSite["isTrusted"]:
                        print(style.BOLD + str(menuCounter) + " " + foundSite["siteName"] + " ♥" + style.END)
                    else:
                        print(style.FAINT + str(menuCounter) + " " + foundSite["siteName"] + style.END )

        print("")
        print(style.BOLD + "0 " + style.END + "Back")    
        print(21 * "-")

        selection = int(getInput("Which site would you like to remove trust from [0-" + str(menuCounter) + "]? ", True))

        if selection > len(siteList):
            print(background.BYELLOW + "Unknown selection" + background.END)
            continue
        elif selection == 0:
            return

        siteToTrust = siteList[selection-1].copy()

        if not siteList[selection-1]["isTrusted"]:
            print(background.BYELLOW + siteList[selection-1]["siteName"] + " is not trusted" + background.END)
            continue

        confirmation = input(background.BMAGENTA + "There is no turning back. " + background.END + "\n" + style.BOLD + "Are you certain you wish to remove the SSL certificate from this site [y/N]? " + style.END).strip()
        if confirmation != "y" and confirmation != "Y":
            # Insufficient confirmations. Return without taking any action.
            print("")
            print(background.BYELLOW + "Certificate removal aborted!" + background.END + style.ITALIC + " (no changes made)" + style.END)
            continue

        # Clear existing configuration except current key and certificate
        siteToTrust["certID"] = ""
        siteToTrust["certKey"] = ""
        siteToTrust["certificate"] = ""
        siteToTrust["certRequest"] = ""
        siteToTrust["certConfig"] = ""
        siteToTrust["certRootKey"] = ""
        siteToTrust["certRoot"] = ""

        removeCertificate(siteToTrust)

        # Update the WordPress database to reflect the http URLs
        updateSiteValues(siteToTrust, "http")

        restartApache()

        # Mark this site as trusted and write the dictionary to the quiver database
        siteToTrust["isTrusted"] = False
        writeSiteConfig(siteToTrust)

        print("")
        print(style.BOLD + siteToTrust["siteName"] + style.END + " is no longer trusted " + style.END)
        print("The site can now only be accessed using http://" + siteToTrust["domainName"] + style.END)




def getCertificate(targetSite):
    # Default to the current certificate key file, if there is one. Otherwise, assume siteName.key
    defaultCertKeyFile = targetSite["certKey"]
    if not defaultCertKeyFile: defaultCertKeyFile = quiverDB + "/certificates/" + targetSite["siteName"] + ".key"
    #print(json.dumps(targetSite, indent=4))

    # Capture the desired key from the user. This should be the absolute path to the signed .key file
    targetSite["certKey"] = input(style.BOLD + "Certificate key (.key) [" + defaultCertKeyFile + "]: " + style.END).strip()
    if not targetSite["certKey"]: targetSite["certKey"] = defaultCertKeyFile

    # Default to the current certificate file, if there is one. Otherwise, assume siteName.crt
    defaultCertFile = targetSite["certificate"]
    if not defaultCertFile: defaultCertFile = quiverDB + "/certificates/" + targetSite["siteName"] + ".crt"

    # Capture the desired certificate from the user. This should be the absolute path to the signed .crt file
    targetSite["certificate"] = input(style.BOLD + "Certificate (.crt) [" + defaultCertFile + "]: " + style.END).strip()
    if not targetSite["certificate"]: targetSite["certificate"] = defaultCertFile

    # Save the dictionary with the updated certificate and key file paths
    writeSiteConfig(targetSite)
    #print(currentSite["importFile"])

    return targetSite



def createRootCertificate(targetSite):
    # Default to the current certificate key file, if there is one. Otherwise, assume siteName.key
    defaultCertKeyFile = targetSite["certRootKey"]
    if not defaultCertKeyFile: defaultCertKeyFile = quiverDB + "/certificates/" + targetSite["siteName"] + "_CA.key"
    #print(json.dumps(targetSite, indent=4))

    # Capture the desired key from the user. This should be the absolute path to the signed .key file
    targetSite["certRootKey"] = input(style.BOLD + "Root Certificate key (.key) [" + defaultCertKeyFile + "]: " + style.END).strip()
    if not targetSite["certRootKey"]: targetSite["certRootKey"] = defaultCertKeyFile

    # Default to the current certificate file, if there is one. Otherwise, assume siteName.crt
    defaultCertRootFile = targetSite["certRoot"]
    if not defaultCertRootFile: defaultCertRootFile = quiverDB + "/certificates/" + targetSite["siteName"] + "_CA.pem"

    # Capture the desired certificate from the user. This should be the absolute path to the signed .pem file
    targetSite["certRoot"] = input(style.BOLD + "Root Certificate (.pem) [" + defaultCertRootFile + "]: " + style.END).strip()
    if not targetSite["certRoot"]: targetSite["certRoot"] = defaultCertRootFile

    # Save the dictionary with the updated certificate and key file paths
    writeSiteConfig(targetSite)
    #print(currentSite["importFile"])

    return targetSite




def createNewCertificates(targetSite):
    certDuration = str(targetSite["certDuration"])
    targetSite["certID"] = str(random.randint(11111111, 99999999))
    selection = getInput("Do you already have a Root CA certificate you would like to use [y/N]? ")

    if (selection == "y") or (selection == "Y"):
        # Get the paths to the certificate files from the user
        targetSite = createRootCertificate(targetSite)
    else:
        print(style.BOLD + "►►► Create Root Key" + style.END)
        targetSite["certRootKey"] = targetSite["certPath"] + "/" + targetSite["siteName"] + "_CA" + targetSite["certID"] + ".key"
        runCommand("openssl genrsa -aes256 -out " + targetSite["certRootKey"] + " 2048")

        print(style.BOLD + "►►► Create Root Certificate" + style.END)
        targetSite["certRoot"] = targetSite["certPath"] + "/" + targetSite["siteName"] + "_CA" + targetSite["certID"] + ".pem"
        oldRunCommand("openssl req -x509 -new -noenc -key " + targetSite["certRootKey"] + " -sha256 -days " + certDuration + " -subj '/C=XX/ST=XX/L=Quiver Locality/O=Fake Quiver Company/OU=Arrows/CN=" + targetSite["domainName"] + "' -out " + targetSite["certRoot"] )

    print(style.BOLD + "►►► Create Website key" + style.END)
    targetSite["certKey"] = targetSite["certPath"] + "/" + targetSite["siteName"] + "_" + targetSite["certID"] + ".key"
    runCommand("openssl genrsa -out " + targetSite["certKey"] + " 2048")

    print(style.BOLD + "►►► Create Certificate Request" + style.END)
    targetSite["certRequest"] = targetSite["certPath"] + "/" + targetSite["siteName"] + "_" + targetSite["certID"] + ".csr"
    oldRunCommand("openssl req -new -key " + targetSite["certKey"] + " -subj '/C=XX/ST=XX/L=Quiver Locality/O=Fake Quiver Company/OU=Arrows/CN=" + targetSite["domainName"] + "' -out " + targetSite["certRequest"] )

    print(style.BOLD + "►►► Create Certificate Configuration File" + style.END)
    targetSite["certConfig"] = targetSite["certPath"] + "/" + targetSite["siteName"] + "_" + targetSite["certID"] + ".ext"
    oldRunCommand("sed 's|__DOMAINNAME__|" + targetSite["domainName"] + "|g' " + quiverHome + "/base/default_cert.ext > " + targetSite["certConfig"])

    print(style.BOLD + "►►► Create Signed Website Certificate" + style.END)
    targetSite["certificate"] = targetSite["certPath"] + "/" + targetSite["siteName"] + "_" + targetSite["certID"] + ".crt"
    runCommand("openssl x509 -req -in " + targetSite["certRequest"] + " -CA " + targetSite["certRoot"] + " -CAkey " + targetSite["certRootKey"] + " -CAcreateserial -out " + targetSite["certificate"] + " -days " + certDuration + " -sha256 -extfile " + targetSite["certConfig"])

    #Save the dictionary with the updated certificate and key file paths
    writeSiteConfig(targetSite)
    #print(currentSite["importFile"])

    print("")
    print("Copy the Root certificate [" + targetSite["certRoot"] + "] to your local machine and added it as a trusted Certificate Authority")
    # Provide instructions on how to do this

    return targetSite



def addCertificate(targetSite):
    print(style.BOLD + "►►► Adding SSL certificate paths to the Apache configuration" + style.END)
    # The config will always start with the default configuration
    # Any user customizations will be overwritten
    shutil.copyfile(quiverHome + "/base/default_https.conf", quiverHome + "/tmp/thttpsconf")

    replaceFileText(quiverHome + "/tmp/thttpsconf", "__CORECONFIG__", targetSite["domainConfig"])
    replaceFileText(quiverHome + "/tmp/thttpsconf", "__CERTKEYFILE__", targetSite["certKey"])
    replaceFileText(quiverHome + "/tmp/thttpsconf", "__CERTFILE__", targetSite["certificate"])

    runCommand("mv " + quiverHome + "/tmp/thttpsconf " + targetSite["apacheConfig"], True)
    runCommand("chown root: " + targetSite["apacheConfig"], True)

    # Enable the site
    runCommand("a2ensite " + targetSite["siteName"], True)

    # Enable the mod_ssl module
    runCommand("a2enmod ssl", True)


def removeCertificate(targetSite):
    print(style.BOLD + "►►► Removing SSL certificate paths from the Apache configuration" + style.END)
    # The config will always start with the default configuration
    # Any user customizations will be overwritten
    shutil.copyfile(quiverHome + "/base/default_http.conf", quiverHome + "/tmp/thttpconf")

    replaceFileText(quiverHome + "/tmp/thttpconf", "__CORECONFIG__", targetSite["domainConfig"])

    runCommand("mv " + quiverHome + "/tmp/thttpconf " + targetSite["apacheConfig"], True)
    runCommand("chown root: " + targetSite["apacheConfig"], True)


def showActiveCertificates(localDatabase = quiverDB):
    print("")
    print(6 * "-" , "Active Certificates" , 6 * "-")

    siteFileList = sorted(os.listdir(localDatabase + "/sites"))
    trustedSiteCount = 0

    for i in siteFileList:
        if i.endswith(".json"):
            with open(quiverDB + "/sites/" + i, 'r') as inFile:
                foundSite = json.load(inFile)

                if foundSite["isTrusted"]:
                    trustedSiteCount += 1
                    print(style.BOLD + "https://" + foundSite["domainName"] + style.END + "\t►►► " + foundSite["certificate"])

    print("")
    if trustedSiteCount == 0:
        print(background.BYELLOW + " No trusted sites found " + background.END)

    #print(style.BOLD + "0 " + style.END + "Back")    
    print(21 * "-")
    print("")

