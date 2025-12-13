
Fish Speech API

 1.5.0 

OAS 3.1

Servers
default
POST
/v1/vqgan/encode
Encode audio using VQGAN model.
Parameters

No parameters
Request body

{
  "audios": [
    "string"
  ]
}

Responses
Code	Description	Links
422	
Media type

[
  {
    "loc": [
      "string"
    ],
    "type": "string",
    "msg": "string",
    "ctx": "string",
    "in": "path"
  }
]

	No links
POST
/v1/vqgan/decode
Decode tokens to audio using VQGAN model.
Parameters

No parameters
Request body

{
  "tokens": [
    [
      [
        0
      ]
    ]
  ]
}

Responses
Code	Description	Links
422	
Media type

[
  {
    "loc": [
      "string"
    ],
    "type": "string",
    "msg": "string",
    "ctx": "string",
    "in": "path"
  }
]

	No links
POST
/v1/tts
Generate speech from text using TTS model.
Parameters

No parameters
Request body

{
  "text": "string",
  "chunk_length": 200,
  "format": "wav",
  "references": [],
  "reference_id": null,
  "seed": null,
  "use_memory_cache": "off",
  "normalize": true,
  "streaming": false,
  "max_new_tokens": 1024,
  "top_p": 0.8,
  "repetition_penalty": 1.1,
  "temperature": 0.8
}

Responses
Code	Description	Links
422	
Media type

[
  {
    "loc": [
      "string"
    ],
    "type": "string",
    "msg": "string",
    "ctx": "string",
    "in": "path"
  }
]

	No links
POST
/v1/references/add
Add a new reference voice with audio file and text.
Parameters

No parameters
Request body
id *
string
	
audio *
string($binary)
	
text *
string
	
Responses
Code	Description	Links
422	
Media type

[
  {
    "loc": [
      "string"
    ],
    "type": "string",
    "msg": "string",
    "ctx": "string",
    "in": "path"
  }
]

	No links
GET
/v1/references/list
Get a list of all available reference voice IDs.
Parameters

No parameters
Responses
Code	Description	Links
DELETE
/v1/references/delete
Delete a reference voice by ID.
Parameters

No parameters
Request body

{
  "reference_id": "string"
}

Responses
Code	Description	Links
422	
Media type

[
  {
    "loc": [
      "string"
    ],
    "type": "string",
    "msg": "string",
    "ctx": "string",
    "in": "path"
  }
]

	No links
POST
/v1/references/update
Rename a reference voice directory from old_reference_id to new_reference_id.
Parameters

No parameters
Request body

{
  "old_reference_id": "string",
  "new_reference_id": "string"
}

Responses
Code	Description	Links
422	
Media type

[
  {
    "loc": [
      "string"
    ],
    "type": "string",
    "msg": "string",
    "ctx": "string",
    "in": "path"
  }
]

	No links
Schemas
object
object
object
object
