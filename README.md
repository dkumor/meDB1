meDB1
=====

Preliminary code for web dashboard. A very basic application for writing 'quantified self' data.
So basic, that to create a user other than me, you need to modify 'meDB/auth.py' line 22 to manually add
a salted and hashed password/user combo. 
You probably also want to change the ssl keys. Y'know, since the private key is public.

The most useful code, in fact, is the dashboard's main javascript, at 'www/js/main.js'.
It defines a nice little framework for asynchronously updating values and adding modules.
