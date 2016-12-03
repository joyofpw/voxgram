<?php
namespace Voices;
/**
* Holds a Voice Object
*/
class Voice {

	public $output;
	public $object;

	public function __construct(\ProcessWire\Page $voice) {

		$this->object = $voice;

		$this->output = [
				'id' => (double) $voice->id,
				'name' => (string) $voice->name,
				'file_id' => (string) $voice->fileId,
				'title' => (string) $voice->fileTitle,
				'username' => (string) $voice->username,
				'emoji' => (string) $voice->about,
				'public' => (bool) $voice->havePublicAccess,
				'tags' => (string) $voice->tags,
				'created_at' => (int) $voice->created,
				'_href' => [
					'path' => (string) $voice->path,
					'self' => (string) $voice->httpUrl,
					'parent' => (string) $voice->parent->httpUrl
				]
			];
	}
}