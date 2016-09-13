<?php
namespace Voices;
/**
* Holds a Voice Object
*/
class Voice {

	public $output;
	public $object;

	public function __construct(\Processwire\Page $voice) {

		$this->object = $voice;

		$this->output = [
				'id' => (double) $voice->id,
				'name' => (string) $voice->name,
				'path' => (string) $voice->path,
				'url' => (string) $voice->httpUrl,
				'file_id' => (string) $voice->fileId,
				'title' => (string) $voice->fileTitle,
				'username' => (string) $voice->username,
				'description' => (string) $voice->description,
				'tags' => (string) $voice->tags,
				'created_at' => (int) $voice->created
			];
	}
}