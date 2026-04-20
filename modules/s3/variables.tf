variable "bucket_name" {
  description = "Nombre único del bucket S3"
  type        = string
}

variable "versioning_enabled" {
  description = "Habilitar versionado en el bucket"
  type        = bool
  default     = true
}

variable "upload_verbs_file" {
  description = "Si true, sube los JSON de verbos al bucket al crear la infra"
  type        = bool
  default     = false
}

variable "irregular_verbs_list" {
  description = "Lista de verbos irregulares en inglés"
  type        = list(string)
  default = [
    "be", "beat", "become", "begin", "bend", "bite", "blow", "break",
    "bring", "build", "buy", "catch", "choose", "come", "cost", "cut",
    "dig", "do", "draw", "drink", "drive", "eat", "fall", "feel",
    "fight", "find", "fly", "forget", "get", "give", "go", "grow",
    "hang", "have", "hear", "hide", "hit", "hold", "hurt", "keep",
    "know", "lay", "lead", "leave", "lend", "let", "lie", "lose",
    "make", "mean", "meet", "pay", "put", "read", "ride", "ring",
    "rise", "run", "say", "see", "sell", "send", "set", "shake",
    "shine", "shoot", "show", "shut", "sing", "sink", "sit", "sleep",
    "speak", "spend", "stand", "steal", "swim", "take", "teach",
    "tell", "think", "throw", "understand", "wake", "wear", "win", "write"
  ]
}

variable "phrasal_verbs_list" {
  description = "Lista de phrasal verbs en inglés"
  type        = list(string)
  default = [
    "break down", "break up", "bring up", "call off", "carry on",
    "catch up", "check in", "check out", "come across", "come up with",
    "cut down", "deal with", "end up", "fall apart", "figure out",
    "fill in", "find out", "get along", "get away", "get back",
    "get over", "get up", "give up", "go ahead", "go through",
    "grow up", "hang on", "hang out", "hold on", "keep up",
    "kick off", "let down", "look after", "look forward to", "look into",
    "look up", "make up", "move on", "pass out", "pick up",
    "point out", "put off", "put on", "run into", "run out of",
    "set up", "show up", "sort out", "take off", "take over",
    "think over", "throw away", "turn down", "turn up", "work out"
  ]
}

variable "tags" {
  description = "Tags comunes aplicados al bucket"
  type        = map(string)
  default     = {}
}
