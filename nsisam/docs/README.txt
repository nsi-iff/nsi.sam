Arquitetura do serviço de armazenamento massivo

	O serviço de armazenamento é responsável por alocar as mídias que serão hospedadas da biblioteca digital.
	Todo o trabalho de armazenamento de dados é feito por um webservice construído utilizando um banco de dados noSQL, o Redis.

	Os métodos utilizados são:

		get_current_user: Método responsável por autenticar e retornar uma tupla com o usuário e a senha.
		
		xmlrpc_get: Recebe como parâmetro uma chave, verifica se esta existe numa lista de bancos, banco por banco, se ela existir, o método retorna o conteúdo armazenado no local referenciado pela chave, se ela não existir, o método não retorna nada.

		xmlrpc_set: Método responsável por guardar conteúdo no banco. Recebe como parâmetro um valor, verifica a autenticação e, caso consiga realizá-la, gera uma chave, escolhe um banco de dados dentre os que estão listados no arquivo “buildout.cfg”, captura a data atual, o usuário da sessão, organiza os dados em um dicionário que contém os dados, o tamanho dos mesmos, a data e o usuário atual, armazena o dicionário no lugar referenciado pela chave gerada e por fim retorna a chave para o usuário para uma possível localização posterior. 

		xmlrpc_update: Método que atualiza os dados do banco. Recebe como parâmetro a chave de localização do arquivo no banco e o novo valor a ser guardado. Da mesma forma que o xmlrpc.set(), ele checa a autenticação, itera na lista de bancos listados, armazena novos dados (data atual, usuário e um dicionário contendo informações do arquivo), armazena os novos valores e retorna a chave de localização.

		xmlrpc_delete: Método responsável por excluir valores do banco. Assim como os outros métodos, também checa a autenticação, caso o usuário seja autenticado, faz uma busca pela chave passada como parâmetro na lista de bancos conhecidos, se a chave existir, o conteúdo armazenado na sua posição é deletado. O valor de retorno é 1(true) caso o arquivo seja excluído com sucesso e 0 (false) caso sejam encontrados problemas na exclusão.



Autor: Eduardo Braga Ferreira Junior.
